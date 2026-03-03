package com.platform;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * AI智能备课平台主应用类
 *
 * 对应Python: backend/src/main.py
 */
@SpringBootApplication
public class AiTeacherPlatformApplication {

    public static void main(String[] args) {
        SpringApplication.run(AiTeacherPlatformApplication.class, args);
    }
}
