package com.aieducenter.studio.interfaces.rest.dto.admin;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 移动工具响应
 *
 * 对应Python: MoveToolResponse
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MoveToolResponse {
    private String message;
    private AdminToolDTO tool;
}
