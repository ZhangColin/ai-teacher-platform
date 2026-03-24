# -*- coding: utf-8 -*-
"""支付定时任务

负责处理订单超时等定时任务
"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.database import SessionLocal
from src.db_models import PaymentOrderModel, PaymentOrderStatus

logger = logging.getLogger(__name__)

# 定时任务调度器
_scheduler = None


def check_expired_orders():
    """
    检查并标记超时订单

    查找所有未支付且已过期的订单，将其状态标记为超时
    """
    db = SessionLocal()

    try:
        now = datetime.now()

        # 查找超时订单
        expired_orders = db.query(PaymentOrderModel).filter(
            PaymentOrderModel.status.in_([
                PaymentOrderStatus.created,
                PaymentOrderStatus.processing
            ]),
            PaymentOrderModel.expire_at < now
        ).all()

        count = 0
        for order in expired_orders:
            order.status = PaymentOrderStatus.timeout
            count += 1
            logger.info(f"订单超时: {order.out_trade_no}")

        if count > 0:
            db.commit()
            logger.info(f"标记 {count} 个订单为超时")

        return count

    except Exception as e:
        logger.error(f"检查超时订单失败: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


def start_scheduler():
    """启动定时任务调度器"""
    import asyncio
    import threading

    global _scheduler

    if _scheduler is not None:
        logger.warning("定时任务调度器已在运行")
        return

    def run_scheduler():
        """运行调度器循环"""
        import time

        logger.info("支付定时任务调度器启动")

        while True:
            try:
                check_expired_orders()
            except Exception as e:
                logger.error(f"定时任务执行失败: {e}", exc_info=True)

            # 每分钟执行一次
            time.sleep(60)

    # 在后台线程中运行
    _scheduler = threading.Thread(target=run_scheduler, daemon=True)
    _scheduler.start()

    logger.info("支付定时任务调度器已启动（每分钟执行一次）")


def stop_scheduler():
    """停止定时任务调度器"""
    global _scheduler
    _scheduler = None
    logger.info("支付定时任务调度器已停止")
