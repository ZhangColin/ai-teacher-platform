-- 初始化支付默认配置
-- 如果配置不存在则插入，存在则跳过

INSERT IGNORE INTO system_configs (key, value, description, created_at, updated_at)
VALUES ('points_per_yuan', '100', '1元对应的积分数量', NOW(), NOW());
