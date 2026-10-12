
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from django.db.models import F
from zoneinfo import ZoneInfo
from django.core.management.color import no_style
from django.db import connection, transaction

import openpyxl
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from demands.models import DeliveryDemand
from masterdata.models import CargoCategory, Outlet, Supplier


DEMAND_SHEET = "17_Delivery_Demands"
USER_SHEET = "02_Users"
EXPECTED_DEMANDS = 700


def normalize_id(value, label):
    """Chỉ chấp nhận ID nguyên hợp lệ, kể cả Excel trả về dạng 1.0."""
    if isinstance(value, bool) or value is None:
        raise CommandError(f"{label}: ID không hợp lệ: {value!r}")

    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise CommandError(f"{label}: ID không hợp lệ: {value!r}")

    if not number.is_finite() or number != number.to_integral_value():
        raise CommandError(f"{label}: ID phải là số nguyên: {value!r}")

    result = int(number)
    if result <= 0:
        raise CommandError(f"{label}: ID phải lớn hơn 0.")

    return result


def read_records(workbook, sheet_name, required_columns):
    if sheet_name not in workbook.sheetnames:
        raise CommandError(f"Thiếu sheet bắt buộc: {sheet_name}")

    rows = workbook[sheet_name].iter_rows(values_only=True)
    header = None
    records = []

    required = set(required_columns)

    for row_number, row in enumerate(rows, start=1):
        values = list(row)
        normalized = [
            str(value).strip() if value is not None else ""
            for value in values
        ]

        if header is None:
            if required.issubset(set(normalized)):
                header = normalized
            continue

        if not any(value is not None for value in values):
            continue

        record = {
            name: values[index] if index < len(values) else None
            for index, name in enumerate(header)
            if name
        }

        # Bỏ qua dòng tiêu đề phụ, dòng trống và dòng không có khóa.
        key = "id" if "id" in record else "demand_code"
        if record.get(key) is None:
            continue

        records.append((row_number, record))

    if header is None:
        raise CommandError(
            f"{sheet_name}: không tìm thấy header có các cột "
            f"{sorted(required)}."
        )

    return records


def required_text(value, label):
    if value is None or not str(value).strip():
        raise CommandError(f"Thiếu trường bắt buộc: {label}.")
    return str(value).strip()


def as_date(value, label):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raise CommandError(f"{label}: ngày không hợp lệ: {value!r}")


def as_time(value, label):
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, time):
        return value
    raise CommandError(f"{label}: giờ không hợp lệ: {value!r}")


def as_datetime(value, label):
    if not isinstance(value, datetime):
        raise CommandError(
            f"{label}: timestamp không hợp lệ: {value!r}"
        )

    source_tz = ZoneInfo("Asia/Ho_Chi_Minh")

    if value.tzinfo is None:
        return value.replace(tzinfo=source_tz)

    return value.astimezone(source_tz)

class Command(BaseCommand):
    help = (
        "Kiểm tra hoặc import 700 delivery demands "
        "từ CoLogi_Dataset.xlsx."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            default="../data/CoLogi_Dataset.xlsx",
            help="Đường dẫn workbook, tính từ thư mục backend.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Ghi dữ liệu sau khi kiểm tra toàn bộ nguồn.",
        )

    def handle(self, *args, **options):
        file_path = Path(options["file"]).resolve()

        if not file_path.is_file():
            raise CommandError(f"Không tìm thấy file: {file_path}")

        workbook = openpyxl.load_workbook(
            file_path,
            read_only=True,
            data_only=True,
        )

        try:
            user_rows = read_records(
                workbook,
                USER_SHEET,
                ["id", "email", "full_name", "is_active"],
            )
            demand_rows = read_records(
                workbook,
                DEMAND_SHEET,
                [
                    "id",
                    "demand_code",
                    "supplier_id",
                    "outlet_id",
                    "cargo_category_id",
                    "quantity_kg",
                    "requested_date",
                    "requested_start_time",
                    "requested_end_time",
                    "status",
                    "created_by",
                    "created_at",
                    "updated_at",
                ],
            )

            if len(user_rows) != 12:
                raise CommandError(
                    f"{USER_SHEET}: mong đợi 12 tài khoản, "
                    f"đọc được {len(user_rows)}."
                )

            if len(demand_rows) != EXPECTED_DEMANDS:
                raise CommandError(
                    f"{DEMAND_SHEET}: mong đợi {EXPECTED_DEMANDS} "
                    f"bản ghi, đọc được {len(demand_rows)}."
                )

            # Ánh xạ ID nguồn của người dùng sang tài khoản Django.
            User = get_user_model()
            user_map = {}
            source_emails = set()

            for row_number, record in user_rows:
                source_id = normalize_id(
                    record["id"], f"{USER_SHEET}, dòng {row_number}"
                )
                email = required_text(
                    record["email"],
                    f"{USER_SHEET}, dòng {row_number}, email",
                ).lower()

                if source_id in user_map:
                    raise CommandError(
                        f"{USER_SHEET}: ID nguồn trùng {source_id}."
                    )
                if email in source_emails:
                    raise CommandError(
                        f"{USER_SHEET}: email trùng {email}."
                    )

                source_emails.add(email)
                user_map[source_id] = email

            db_users = {
                user.email.lower(): user
                for user in User.objects.filter(email__in=source_emails)
            }

            missing_emails = source_emails - set(db_users)
            if missing_emails:
                raise CommandError(
                    "Không tìm thấy tài khoản Django cho các email nguồn: "
                    f"{sorted(missing_emails)}."
                )

            # Kiểm tra ID nguồn không bị gán nhầm sang tài khoản khác.
            source_user_ids = {}
            for source_id, email in user_map.items():
                source_user_ids[source_id] = db_users[email]

            supplier_ids = set()
            outlet_ids = set()
            category_ids = set()
            demand_codes = set()
            demand_ids = set()
            prepared = []

            valid_statuses = {choice[0] for choice in DeliveryDemand.Status.choices}

            for row_number, record in demand_rows:
                label = f"{DEMAND_SHEET}, dòng {row_number}"

                source_id = normalize_id(record["id"], label)
                supplier_id = normalize_id(record["supplier_id"], label)
                outlet_id = normalize_id(record["outlet_id"], label)
                category_id = normalize_id(
                    record["cargo_category_id"], label
                )
                created_by_source_id = normalize_id(
                    record["created_by"], label
                )

                if source_id in demand_ids:
                    raise CommandError(f"{label}: ID demand bị trùng.")
                demand_ids.add(source_id)

                demand_code = required_text(
                    record["demand_code"], f"{label}, demand_code"
                )
                if demand_code in demand_codes:
                    raise CommandError(
                        f"{label}: demand_code bị trùng {demand_code}."
                    )
                demand_codes.add(demand_code)

                if created_by_source_id not in source_user_ids:
                    raise CommandError(
                        f"{label}: created_by={created_by_source_id} "
                        "không tồn tại trong sheet 02_Users."
                    )

                try:
                    quantity = Decimal(str(record["quantity_kg"]))
                except (InvalidOperation, ValueError):
                    raise CommandError(
                        f"{label}: quantity_kg không hợp lệ."
                    )

                if not quantity.is_finite() or quantity <= 0:
                    raise CommandError(
                        f"{label}: quantity_kg phải lớn hơn 0."
                    )

                requested_date = as_date(
                    record["requested_date"], f"{label}, requested_date"
                )
                start_time = as_time(
                    record["requested_start_time"],
                    f"{label}, requested_start_time",
                )
                end_time = as_time(
                    record["requested_end_time"],
                    f"{label}, requested_end_time",
                )

                if end_time <= start_time:
                    raise CommandError(
                        f"{label}: giờ kết thúc phải sau giờ bắt đầu."
                    )

                status = required_text(
                    record["status"], f"{label}, status"
                )
                if status not in valid_statuses:
                    raise CommandError(
                        f"{label}: status không hợp lệ: {status!r}."
                    )

                created_at = as_datetime(
                    record["created_at"], f"{label}, created_at"
                )
                updated_at = as_datetime(
                    record["updated_at"], f"{label}, updated_at"
                )

                if updated_at < created_at:
                    raise CommandError(
                        f"{label}: updated_at sớm hơn created_at."
                    )

                supplier_ids.add(supplier_id)
                outlet_ids.add(outlet_id)
                category_ids.add(category_id)

                prepared.append(
                    {
                        "source_id": source_id,
                        "demand_code": demand_code,
                        "supplier_id": supplier_id,
                        "outlet_id": outlet_id,
                        "category_id": category_id,
                        "quantity": quantity,
                        "requested_date": requested_date,
                        "start_time": start_time,
                        "end_time": end_time,
                        "status": status,
                        "notes": record.get("notes"),
                        "created_by": source_user_ids[created_by_source_id],
                        "created_at": created_at,
                        "updated_at": updated_at,
                    }
                )

            # Đối chiếu toàn bộ khóa ngoại với database.
            existing_suppliers = set(
                Supplier.objects.filter(pk__in=supplier_ids)
                .values_list("pk", flat=True)
            )
            existing_outlets = set(
                Outlet.objects.filter(pk__in=outlet_ids)
                .values_list("pk", flat=True)
            )
            existing_categories = set(
                CargoCategory.objects.filter(pk__in=category_ids)
                .values_list("pk", flat=True)
            )

            if supplier_ids - existing_suppliers:
                raise CommandError(
                    f"Supplier ID thiếu: {sorted(supplier_ids - existing_suppliers)}"
                )
            if outlet_ids - existing_outlets:
                raise CommandError(
                    f"Outlet ID thiếu: {sorted(outlet_ids - existing_outlets)}"
                )
            if category_ids - existing_categories:
                raise CommandError(
                    "CargoCategory ID thiếu: "
                    f"{sorted(category_ids - existing_categories)}"
                )

            existing_codes = set(
                DeliveryDemand.objects.filter(
                    demand_code__in=demand_codes
                ).values_list("demand_code", flat=True)
            )
            if existing_codes:
                raise CommandError(
                    f"Demand code đã tồn tại: {sorted(existing_codes)[:10]}."
                )

            current_count = DeliveryDemand.objects.count()
            if current_count:
                raise CommandError(
                    f"Bảng DeliveryDemand hiện có {current_count} bản ghi. "
                    "Lệnh này chỉ hỗ trợ import vào bảng trống."
                )

            self.stdout.write(f"Workbook: {file_path}")
            self.stdout.write(f"Demand hợp lệ: {len(prepared)}")
            self.stdout.write(f"Supplier đối chiếu: {len(supplier_ids)}")
            self.stdout.write(f"Outlet đối chiếu: {len(outlet_ids)}")
            self.stdout.write(
                f"Cargo category đối chiếu: {len(category_ids)}"
            )
            self.stdout.write(
                "created_by đã ánh xạ theo email từ sheet 02_Users."
            )
            self.stdout.write(
                "Timestamp nguồn sẽ được khôi phục sau khi tạo bản ghi."
            )

            if not options["apply"]:
                self.stdout.write(
                    self.style.SUCCESS(
                        "DRY RUN hoàn tất. Database chưa bị thay đổi. "
                        "Chạy lại với --apply khi đã sẵn sàng."
                    )
                )
                return

            with transaction.atomic():
                # Khóa bảng logic bằng cách kiểm tra lại ngay trước khi ghi.
                if DeliveryDemand.objects.exists():
                    raise CommandError(
                        "DeliveryDemand không còn trống; đã hủy import."
                    )

                objects = [
                    DeliveryDemand(
                        id=item["source_id"],
                        demand_code=item["demand_code"],
                        supplier_id=item["supplier_id"],
                        outlet_id=item["outlet_id"],
                        cargo_category_id=item["category_id"],
                        quantity_kg=item["quantity"],
                        requested_date=item["requested_date"],
                        requested_start_time=item["start_time"],
                        requested_end_time=item["end_time"],
                        status=item["status"],
                        notes=item["notes"],
                        created_by=item["created_by"],
                    )
                    for item in prepared
                ]

                DeliveryDemand.objects.bulk_create(
                    objects,
                    batch_size=200,
                )

                # auto_now_add/auto_now được áp dụng khi INSERT.
                # QuerySet.update() cho phép khôi phục timestamp nguồn.
                for item in prepared:
                    DeliveryDemand.objects.filter(
                        pk=item["source_id"]
                    ).update(
                        created_at=item["created_at"],
                        updated_at=item["updated_at"],
                    )


                if DeliveryDemand.objects.count() != EXPECTED_DEMANDS:
                    raise CommandError(
                        "Số bản ghi sau import không bằng 700; rollback."
                    )

                if DeliveryDemand.objects.filter(
                    requested_end_time__lte=F("requested_start_time")
                ).exists():
                    raise CommandError(
                        "Phát hiện khung giờ không hợp lệ sau import."
                    )

                # Đồng bộ sequence sau khi chèn ID nguồn 1–700.
                sequence_sql = connection.ops.sequence_reset_sql(
                    no_style(),
                    [DeliveryDemand],
                )

                with connection.cursor() as cursor:
                    for sql in sequence_sql:
                        cursor.execute(sql)


            self.stdout.write(
                self.style.SUCCESS(
                    f"Import thành công {EXPECTED_DEMANDS} delivery demands."
                )
            )

        finally:
            workbook.close()
