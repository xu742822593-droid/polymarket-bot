import os, logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler,
    CallbackQueryHandler, ContextTypes
)
import polymarket as pm

load_dotenv()
logging.basicConfig(level=logging.INFO)

ALLOWED = int(os.getenv("TG_ALLOWED_USER_ID", "0"))
TOKEN = os.getenv("TG_BOT_TOKEN")


def auth(fn):
    async def wrap(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != ALLOWED:
            await update.message.reply_text("⛔ 无权限")
            return
        return await fn(update, ctx)
    return wrap


@auth
async def cmd_start(update, ctx):
    await update.message.reply_text(
        "🤖 PolyBot 已就绪\n\n"
        "/search <词> — 搜索市场\n"
        "/price <token_id> — 查价格\n"
        "/buy <id> <价> <量> — 买入\n"
        "/sell <id> <价> <量> — 卖出\n"
        "/orders — 当前挂单\n"
        "/history — 下单记录\n"
        "/cancelall — 取消所有单\n"
        "/status — 运行状态"
    )


@auth
async def cmd_search(update, ctx):
    if not ctx.args:
        await update.message.reply_text("用法: /search bitcoin")
        return
    markets = pm.search_markets(" ".join(ctx.args))
    if not markets:
        await update.message.reply_text("❌ 未找到市场")
        return
    for m in markets:
        text = f"📌 {m['question']}\n截止: {m['end_date']}\n"
        for t in m["tokens"]:
            text += f"  {t['outcome']}: {t['token_id'][:24]}...\n"
        await update.message.reply_text(text)


@auth
async def cmd_price(update, ctx):
    if not ctx.args:
        await update.message.reply_text("用法: /price <token_id>")
        return
    info = pm.get_price_info(ctx.args[0])
    if not info:
        await update.message.reply_text("❌ 获取失败")
        return
    kb = [[InlineKeyboardButton(
        f"✅ 快速买入 @ {info.get('ask','?')}",
        callback_data=f"qbuy|{ctx.args[0]}|{info.get('ask',0.5)}"
    )]]
    await update.message.reply_text(
        f"💹 买价: {info.get('bid')}\n"
        f"卖价: {info.get('ask')}\n"
        f"中间: {info.get('mid')}\n"
        f"价差: {info.get('spread')}",
        reply_markup=InlineKeyboardMarkup(kb)
    )


@auth
async def cmd_buy(update, ctx):
    if len(ctx.args) < 3:
        await update.message.reply_text("用法: /buy <token_id> <价格> <USDC>")
        return
    tid, price, size = ctx.args[0], ctx.args[1], ctx.args[2]
    kb = [[
        InlineKeyboardButton("✅ 确认买入", callback_data=f"cbuy|{tid}|{price}|{size}"),
        InlineKeyboardButton("❌ 取消", callback_data="cancel"),
    ]]
    await update.message.reply_text(
        f"确认买入?\nToken: {tid[:24]}...\n价格: {price}  金额: {size} USDC",
        reply_markup=InlineKeyboardMarkup(kb)
    )


@auth
async def cmd_sell(update, ctx):
    if len(ctx.args) < 3:
        await update.message.reply_text("用法: /sell <token_id> <价格> <USDC>")
        return
    tid, price, size = ctx.args[0], ctx.args[1], ctx.args[2]
    kb = [[
        InlineKeyboardButton("✅ 确认卖出", callback_data=f"csell|{tid}|{price}|{size}"),
        InlineKeyboardButton("❌ 取消", callback_data="cancel"),
    ]]
    await update.message.reply_text(
        f"确认卖出?\nToken: {tid[:24]}...\n价格: {price}  金额: {size} USDC",
        reply_markup=InlineKeyboardMarkup(kb)
    )


@auth
async def cmd_orders(update, ctx):
    orders = pm.get_open_orders()
    if not orders:
        await update.message.reply_text("📭 无挂单")
        return
    text = f"📋 挂单 {len(orders)} 条\n\n"
    for o in orders[:5]:
        text += f"价格:{o.get('price')}  量:{o.get('original_size')} USDC\n已成交:{o.get('size_matched','0')}\n\n"
    await update.message.reply_text(text)


@auth
async def cmd_history(update, ctx):
    h = pm.get_history()
    if not h:
        await update.message.reply_text("📭 无记录")
        return
    text = "🗂 最近下单\n\n"
    for o in reversed(h):
        text += f"{o['side']} @ {o['price']} x {o['size']} USDC\n{o['time']}  {o['status']}\n\n"
    await update.message.reply_text(text)


@auth
async def cmd_cancelall(update, ctx):
    kb = [[
        InlineKeyboardButton("🗑 确认取消全部", callback_data="ccancel"),
        InlineKeyboardButton("❌ 不取消", callback_data="cancel"),
    ]]
    await update.message.reply_text("确认取消所有挂单？", reply_markup=InlineKeyboardMarkup(kb))


@auth
async def cmd_status(update, ctx):
    orders = pm.get_open_orders()
    h = pm.get_history(limit=100)
    await update.message.reply_text(
        f"🟢 Bot 运行中\n"
        f"当前挂单: {len(orders)} 条\n"
        f"历史总单: {len(h)} 条"
    )


async def on_callback(update, ctx):
    q = update.callback_query
    await q.answer()
    d = q.data
    if d == "cancel":
        await q.edit_message_text("已取消")
    elif d == "ccancel":
        ok = pm.cancel_all_orders()
        await q.edit_message_text("✅ 所有挂单已取消" if ok else "❌ 取消失败")
    elif d.startswith("qbuy|"):
        _, tid, price = d.split("|")
        size = float(os.getenv("DEFAULT_BET_USDC", "1.0"))
        r = pm.place_order(tid, float(price), size, "BUY")
        await q.edit_message_text(
            f"✅ 已下单 {size} USDC @ {price}" if r["success"] else f"❌ {r['error']}"
        )
    elif d.startswith("cbuy|") or d.startswith("csell|"):
        parts = d.split("|")
        side = "BUY" if parts[0] == "cbuy" else "SELL"
        r = pm.place_order(parts[1], float(parts[2]), float(parts[3]), side)
        await q.edit_message_text(
            f"✅ 订单成功 {r.get('order_id','')}" if r["success"] else f"❌ {r['error']}"
        )


async def main():
    app = Application.builder().token(TOKEN).build()
    for cmd, fn in [
        ("start", cmd_start), ("help", cmd_start),
        ("search", cmd_search), ("price", cmd_price),
        ("buy", cmd_buy), ("sell", cmd_sell),
        ("orders", cmd_orders), ("history", cmd_history),
        ("cancelall", cmd_cancelall), ("status", cmd_status),
    ]:
        app.add_handler(CommandHandler(cmd, fn))
    app.add_handler(CallbackQueryHandler(on_callback))
    print("🤖 Bot 启动成功")
    await app.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
