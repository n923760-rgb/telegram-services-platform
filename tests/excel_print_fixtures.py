from app.builders.schema import Table


def wide_table(*, arabic=False):
    columns = (
        [
            "المرجع",
            "وصف التسليم",
            "ملاحظات العمليات",
            "ملاحظات المورد",
            "ملاحظات العميل",
            "ملاحظات المراجعة",
        ]
        if arabic
        else [
            "Reference",
            "Delivery description",
            "Operations notes",
            "Supplier notes",
            "Customer notes",
            "Review notes",
        ]
    )
    note = (
        "تتضمن هذه الملاحظة تفاصيل متطلبات التسليم الأصلية وسياق المتابعة والمراجعة دون تغيير المعلومات. "
        if arabic
        else "This detailed source note preserves the original delivery requirements and review context. "
    )
    return Table(
        title="متابعة التسليم" if arabic else "Delivery follow up",
        columns=columns,
        rows=[[f"{123 + i:05d}", *[note + f"FIELD{j}ROW{i}" for j in range(5)]] for i in range(2)],
    )
