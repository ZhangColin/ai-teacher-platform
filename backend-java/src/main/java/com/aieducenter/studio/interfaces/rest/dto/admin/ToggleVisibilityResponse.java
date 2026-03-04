package com.platform.interfaces.rest.dto.admin;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 切换可见性响应
 *
 * 对应Python: ToggleVisibilityResponse
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ToggleVisibilityResponse {
    private String message;
    private AdminToolDTO tool;
}
