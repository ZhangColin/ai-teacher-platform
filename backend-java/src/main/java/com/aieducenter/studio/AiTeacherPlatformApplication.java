package com.platform;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.web.reactive.WebFluxAutoConfiguration;

/**
 * AI智能备课平台主应用类
 *
 * 对应Python: backend/src/main.py
 */
@SpringBootApplication(exclude = WebFluxAutoConfiguration.class)
public class AiTeacherPlatformApplication {

    public static void main(String[] args) {
        SpringApplication.run(AiTeacherPlatformApplication.class, args);
    }
}
