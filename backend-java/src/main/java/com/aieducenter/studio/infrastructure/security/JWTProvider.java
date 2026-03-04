package com.aieducenter.studio.infrastructure.security;

import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import lombok.Getter;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.time.Duration;
import java.time.Instant;
import java.util.Date;

/**
 * JWT提供者
 *
 * 对应Python: backend/src/services/auth_service.py
 * 负责JWT的生成和验证
 *
 * @author AI Teacher Platform
 */
@Component
@Getter
public class JWTProvider {

    private final SecretKey secretKey;
    private final Duration defaultExpiration;
    private final Duration longLivedExpiration;
    private final JwtParser parser;
    private final JwtBuilder builder;

    /**
     * 构造函数
     *
     * @param secretKey JWT密钥（从配置注入）
     * @param defaultExpiration 默认过期时间（从配置注入）
     * @param longLivedExpiration 长期Token过期时间（从配置注入）
     */
    public JWTProvider(
            @Value("${jwt.secret}") String secretKey,
            @Value("${jwt.expiration:86400000}") long defaultExpirationMs,
            @Value("${jwt.long-lived-expiration:604800000}") long longLivedExpirationMs
    ) {
        // 验证密钥强度（至少32字符）
        if (secretKey == null || secretKey.length() < 32) {
            throw new IllegalArgumentException(
                "JWT密钥必须至少32字符。当前长度: " + (secretKey != null ? secretKey.length() : 0) + "\n" +
                "生成方法: 使用 Python: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            );
        }

        this.secretKey = Keys.hmacShaKeyFor(secretKey.getBytes());
        this.defaultExpiration = Duration.ofMillis(defaultExpirationMs);
        this.longLivedExpiration = Duration.ofMillis(longLivedExpirationMs);
        this.parser = Jwts.parserBuilder()
            .setSigningKey(this.secretKey)
            .build();
        this.builder = Jwts.builder()
            .signWith(this.secretKey, SignatureAlgorithm.HS512);
    }

    /**
     * 生成JWT Token
     * 对应Python: generate_token(user: User, remember_me: bool = False) -> str
     *
     * @param userId 用户ID
     * @param rememberMe 是否记住我（影响Token有效期）
     * @return JWT Token
     */
    public String generateToken(String userId, boolean rememberMe) {
        Instant now = Instant.now();
        Duration expiration = rememberMe ? this.longLivedExpiration : this.defaultExpiration;
        Instant expiry = now.plus(expiration);

        return builder
            .setSubject(userId)
            .setIssuedAt(Date.from(now))
            .setExpiration(Date.from(expiry))
            .compact();
    }

    /**
     * 生成长期Token（记住我，7天有效期）
     * 对应Python: generate_token(..., remember_me=True)
     *
     * @param userId 用户ID
     * @return JWT Token（7天有效期）
     */
    public String generateLongLivedToken(String userId) {
        return generateToken(userId, true);
    }

    /**
     * 生成短期Token（24小时有效期）
     * 对应Python: generate_token(..., remember_me=False)
     *
     * @param userId 用户ID
     * @return JWT Token（24小时有效期）
     */
    public String generateShortLivedToken(String userId) {
        return generateToken(userId, false);
    }

    /**
     * 验证Token并返回用户ID
     * 对应Python: verify_token(token: str) -> Optional[Dict]
     *
     * @param token JWT Token
     * @return 用户ID，如果Token无效或过期抛出JwtException
     * @throws JwtException Token无效或过期
     */
    public String validateTokenAndGetUserId(String token) throws JwtException {
        Jws<Claims> claims = parser.parseClaimsJws(token);
        return claims.getBody().getSubject();
    }

    /**
     * 验证Token（不抛出异常）
     * 对应Python: verify_token(token: str) -> Optional[Dict]
     *
     * @param token JWT Token
     * @return 用户ID，如果Token无效或过期返回null
     */
    public String validateToken(String token) {
        try {
            return validateTokenAndGetUserId(token);
        } catch (JwtException e) {
            return null;
        }
    }

    /**
     * 从Token中提取用户ID（不验证签名）
     * 对应Python: get_user_id_from_token(token: str) -> Optional[str]
     *
     * 注意：此方法不验证Token签名和过期时间，仅用于提取信息
     *
     * @param token JWT Token
     * @return 用户ID（可能为null）
     */
    public String getUserIdFromToken(String token) {
        try {
            // 不验证签名，只解析
            int firstDot = token.indexOf('.');
            int lastDot = token.lastIndexOf('.');
            if (firstDot <= 0 || lastDot <= firstDot) {
                return null;
            }

            String payloadStr = token.substring(firstDot + 1, lastDot);
            byte[] payloadBytes = java.util.Base64.getUrlDecoder().decode(payloadStr);

            com.fasterxml.jackson.databind.ObjectMapper mapper = new com.fasterxml.jackson.databind.ObjectMapper();
            com.fasterxml.jackson.databind.JsonNode payload = mapper.readTree(payloadBytes);

            return payload.get("sub").asText();
        } catch (Exception e) {
            return null;
        }
    }
}
