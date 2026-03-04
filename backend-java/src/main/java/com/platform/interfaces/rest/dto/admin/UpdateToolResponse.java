package com.platform.interfaces.rest.dto.admin;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 更新工具响应
 *
 * 对应Python: UpdateToolResponse
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UpdateToolResponse {
    private AdminToolDTO tool;
}
