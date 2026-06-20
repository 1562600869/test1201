from datetime import datetime

TEA_TYPES = ["绿茶", "红茶", "白茶", "乌龙", "普洱", "花茶"]


class ValidationError(Exception):
    pass


def validate_tea_type(tea_type):
    if tea_type not in TEA_TYPES:
        raise ValidationError(
            f"茶叶类型必须是以下之一：{', '.join(TEA_TYPES)}"
        )


def validate_positive_int(value, name):
    try:
        v = int(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{name}必须是整数")
    if v <= 0:
        raise ValidationError(f"{name}必须是正整数")
    return v


def validate_non_negative_int(value, name):
    try:
        v = int(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{name}必须是整数")
    if v < 0:
        raise ValidationError(f"{name}不能为负数")
    return v


def validate_date(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        raise ValidationError("日期格式错误，应为 YYYY-MM-DD")


def validate_month(month_str):
    try:
        dt = datetime.strptime(month_str, "%Y-%m")
        return dt.strftime("%Y-%m")
    except ValueError:
        raise ValidationError("月份格式错误，应为 YYYY-MM")


def add_tea(data, tea_id, name, tea_type, unit, stock, cost, price):
    if not tea_id or not name:
        raise ValidationError("茶叶ID和名称不能为空")

    validate_tea_type(tea_type)
    stock = validate_non_negative_int(stock, "初始库存")
    cost = validate_non_negative_int(cost, "进货价")
    price = validate_non_negative_int(price, "零售价")

    if tea_id in data["teas"]:
        raise ValidationError(f"茶叶ID {tea_id} 已存在")

    data["teas"][tea_id] = {
        "id": tea_id,
        "name": name,
        "type": tea_type,
        "unit": unit,
        "stock": stock,
        "cost": cost,
        "price": price,
    }
    return data["teas"][tea_id]


def restock_tea(data, tea_id, qty, cost):
    if tea_id not in data["teas"]:
        raise ValidationError(f"茶叶ID {tea_id} 不存在")

    qty = validate_positive_int(qty, "补货数量")
    cost = validate_positive_int(cost, "补货成本")

    tea = data["teas"][tea_id]
    tea["stock"] += qty
    tea["cost"] = cost

    data["restocks"].append({
        "tea_id": tea_id,
        "qty": qty,
        "cost": cost,
        "date": datetime.now().strftime("%Y-%m-%d"),
    })
    return tea


def sell_tea(data, tea_id, qty, date):
    if tea_id not in data["teas"]:
        raise ValidationError(f"茶叶ID {tea_id} 不存在")

    qty = validate_positive_int(qty, "销售数量")
    date = validate_date(date)

    tea = data["teas"][tea_id]
    if tea["stock"] < qty:
        shortage = qty - tea["stock"]
        raise ValidationError(
            f"库存不足，当前库存 {tea['stock']} {tea['unit']}，"
            f"还需 {shortage} {tea['unit']}"
        )

    tea["stock"] -= qty
    profit = (tea["price"] - tea["cost"]) * qty

    data["sales"].append({
        "tea_id": tea_id,
        "qty": qty,
        "date": date,
        "unit_price": tea["price"],
        "unit_cost": tea["cost"],
        "profit": profit,
    })
    return {
        "tea": tea,
        "qty": qty,
        "profit": profit,
    }


def low_stock(data, threshold):
    threshold = validate_non_negative_int(threshold, "阈值")
    result = []
    for tea_id, tea in sorted(data["teas"].items()):
        if tea["stock"] <= threshold:
            result.append(tea)
    return result


def monthly_profit(data, month):
    month = validate_month(month)
    by_type = {}

    for sale in data["sales"]:
        sale_month = sale["date"][:7]
        if sale_month != month:
            continue

        tea_id = sale["tea_id"]
        tea = data["teas"].get(tea_id)
        if not tea:
            continue

        tea_type = tea["type"]
        if tea_type not in by_type:
            by_type[tea_type] = {
                "type": tea_type,
                "total_qty": 0,
                "total_profit": 0,
            }
        by_type[tea_type]["total_qty"] += sale["qty"]
        by_type[tea_type]["total_profit"] += sale["profit"]

    return sorted(by_type.values(), key=lambda x: x["type"])
