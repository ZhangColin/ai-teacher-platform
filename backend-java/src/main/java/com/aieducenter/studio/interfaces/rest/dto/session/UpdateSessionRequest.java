package com.aieducenter.studio.interfaces.rest.dto.session;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 更新会话请求
 *
 * 对应Python: UpdateSessionRequest
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UpdateSessionRequest {
    @NotBlank(message = "标题不能为空")
    private String title;
}
