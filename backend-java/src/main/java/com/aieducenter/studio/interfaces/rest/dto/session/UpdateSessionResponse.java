package com.aieducenter.studio.interfaces.rest.dto.session;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 更新会话响应
 *
 * 对应Python: UpdateSessionResponse
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UpdateSessionResponse {
    private String sessionId;
    private String title;
}
