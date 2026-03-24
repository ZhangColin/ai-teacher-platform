/** 支付相关 API */
import apiClient from './apiClient'

/**
 * 创建订单请求
 */
export interface CreateOrderRequest {
  amount: number // 单位：分
}

/**
 * 支付订单
 */
export interface PaymentOrder {
  id: string
  out_trade_no: string
  amount: number
  status: string
  qr_code_data?: string
  expire_at?: string
  created_at: string
}

/**
 * 充值记录
 */
export interface RechargeRecord {
  id: string
  amount: number
  points: number
  created_at: string
}

/**
 * 充值记录列表响应
 */
export interface RechargeListResponse {
  items: RechargeRecord[]
  total: number
}

/**
 * 支付 API
 */
export const paymentApi = {
  /**
   * 创建支付订单
   */
  createOrder: (data: CreateOrderRequest) =>
    apiClient.post<PaymentOrder>('/payment/create-order', data),

  /**
   * 查询订单状态
   */
  queryOrder: (orderId: string) =>
    apiClient.get<PaymentOrder>(`/payment/order/${orderId}`),

  /**
   * 获取我的充值记录
   */
  getMyRecharges: (page = 1, pageSize = 20) =>
    apiClient.get<RechargeListResponse>('/payment/my-recharges', {
      params: { page, page_size: pageSize }
    })
}

export default paymentApi
