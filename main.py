import argparse
import sys

from storage import load_data, save_data, atomic_update, DATA_FILE
from models import (
    ValidationError,
    TeaType,
    TEA_TYPES,
    add_tea,
    restock_tea,
    sell_tea,
    low_stock,
    monthly_profit,
)


def cmd_add_tea(args):
    def updater(data):
        return add_tea(
            data,
            tea_id=args.tea_id,
            name=args.name,
            tea_type=args.type,
            unit=args.unit,
            stock=args.stock,
            cost=args.cost,
            price=args.price,
        )

    tea = atomic_update(updater)
    print(f"已添加茶叶：{tea['id']} {tea['name']} ({tea['type']})")
    print(f"  库存：{tea['stock']} {tea['unit']}")
    print(f"  进货价：{tea['cost']} 分/{tea['unit']}")
    print(f"  零售价：{tea['price']} 分/{tea['unit']}")


def cmd_restock(args):
    def updater(data):
        return restock_tea(
            data,
            tea_id=args.tea_id,
            qty=args.qty,
            cost=args.cost,
        )

    tea = atomic_update(updater)
    print(f"补货成功：{tea['id']} {tea['name']}")
    print(f"  当前库存：{tea['stock']} {tea['unit']}")
    print(f"  当前进货价：{tea['cost']} 分/{tea['unit']}")


def cmd_sell(args):
    def updater(data):
        return sell_tea(
            data,
            tea_id=args.tea_id,
            qty=args.qty,
            date=args.date,
        )

    result = atomic_update(updater)
    tea = result["tea"]
    print(f"销售成功：{tea['id']} {tea['name']}")
    print(f"  销售数量：{result['qty']} {tea['unit']}")
    print(f"  剩余库存：{tea['stock']} {tea['unit']}")
    print(f"  毛利：{result['profit']} 分")


def cmd_low_stock(args):
    data = load_data()
    teas = low_stock(data, args.threshold)
    if not teas:
        print(f"没有库存低于或等于 {args.threshold} 的茶叶")
        return

    print(f"库存低于或等于 {args.threshold} 的茶叶：")
    print("-" * 60)
    for tea in teas:
        print(f"  {tea['id']}  {tea['name']:<10}  {tea['type']:<4}  "
              f"库存: {tea['stock']} {tea['unit']}")


def cmd_monthly_profit(args):
    data = load_data()
    results = monthly_profit(data, args.month)
    if not results:
        print(f"{args.month} 月没有销售记录")
        return

    print(f"{args.month} 月各茶叶类型销售统计：")
    print("-" * 60)
    print(f"{'类型':<6}  {'销售量':>10}  {'毛利(分)':>12}  {'毛利(元)':>12}")
    print("-" * 60)
    total_qty = 0
    total_profit = 0
    for r in results:
        profit_yuan = r["total_profit"] / 100
        print(f"{r['type']:<6}  {r['total_qty']:>10}  "
              f"{r['total_profit']:>12}  {profit_yuan:>12.2f}")
        total_qty += r["total_qty"]
        total_profit += r["total_profit"]
    print("-" * 60)
    print(f"{'合计':<6}  {total_qty:>10}  "
          f"{total_profit:>12}  {total_profit / 100:>12.2f}")


def main():
    parser = argparse.ArgumentParser(
        description="茶叶店进货与零售管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    p_add = subparsers.add_parser("add-tea", help="添加新茶叶")
    p_add.add_argument("tea_id", help="茶叶编号")
    p_add.add_argument("name", help="茶叶名称")
    p_add.add_argument("--type", required=True, choices=TeaType.values(),
                       help=f"茶叶类型：{', '.join(TeaType.values())}")
    p_add.add_argument("--unit", required=True, help="计量单位（如 g）")
    p_add.add_argument("--stock", type=int, default=0, help="初始库存")
    p_add.add_argument("--cost", type=int, required=True, help="进货价（分/单位）")
    p_add.add_argument("--price", type=int, required=True, help="零售价（分/单位）")
    p_add.set_defaults(func=cmd_add_tea)

    p_restock = subparsers.add_parser("restock", help="补货")
    p_restock.add_argument("tea_id", help="茶叶编号")
    p_restock.add_argument("--qty", type=int, required=True, help="补货数量")
    p_restock.add_argument("--cost", type=int, required=True, help="补货成本（分/单位）")
    p_restock.set_defaults(func=cmd_restock)

    p_sell = subparsers.add_parser("sell", help="销售")
    p_sell.add_argument("tea_id", help="茶叶编号")
    p_sell.add_argument("--qty", type=int, required=True, help="销售数量")
    p_sell.add_argument("--date", required=True, help="销售日期 (YYYY-MM-DD)")
    p_sell.set_defaults(func=cmd_sell)

    p_low = subparsers.add_parser("low-stock", help="查看低库存茶叶")
    p_low.add_argument("--threshold", type=int, required=True, help="库存阈值")
    p_low.set_defaults(func=cmd_low_stock)

    p_profit = subparsers.add_parser("monthly-profit", help="月度利润统计")
    p_profit.add_argument("--month", required=True, help="月份 (YYYY-MM)")
    p_profit.set_defaults(func=cmd_monthly_profit)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except ValidationError as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"系统错误：{e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
