package com.platform.interfaces.rest.dto.admin;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 创建工具响应
 *
 * 对应Python: CreateToolResponse
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CreateToolResponse {
    private AdminToolDTO tool;
}
