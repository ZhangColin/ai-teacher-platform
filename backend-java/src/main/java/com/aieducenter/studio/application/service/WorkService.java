package com.aieducenter.studio.application.service;

import com.aieducenter.studio.infrastructure.persistence.jpa.WorkCategoryEntity;
import com.aieducenter.studio.infrastructure.persistence.jpa.WorkEntity;
import com.aieducenter.studio.infrastructure.persistence.jpa.WorkCategoryJpaRepository;
import com.aieducenter.studio.infrastructure.persistence.jpa.WorkJpaRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * 作品服务
 *
 * 对应Python: backend/src/services/work_service.py
 */
@Service
public class WorkService {

    private final WorkCategoryJpaRepository categoryRepository;
    private final WorkJpaRepository workRepository;

    public WorkService(
            WorkCategoryJpaRepository categoryRepository,
            WorkJpaRepository workRepository
    ) {
        this.categoryRepository = categoryRepository;
        this.workRepository = workRepository;
    }

    public List<CategoryWithWorks> getCategoriesWithWorks() {
        return categoryRepository.findAllByOrderByOrderAsc().stream()
            .map(category -> {
                List<WorkEntity> works = workRepository
                    .findByCategoryIdAndVisibleTrueOrderByOrderAsc(category.getId());

                if (works.isEmpty()) {
                    return null;
                }

                return new CategoryWithWorks(
                    category.getId(),
                    category.getName(),
                    category.getIcon(),
                    category.getOrder(),
                    works.stream()
                        .map(work -> new WorkListItem(
                            work.getId(),
                            work.getName(),
                            work.getDescription(),
                            work.getIcon(),
                            work.getHtmlPath(),
                            work.getOrder()
                        ))
                        .collect(Collectors.toList())
                );
            })
            .filter(java.util.Objects::nonNull)
            .collect(Collectors.toList());
    }

    public WorkEntity getWorkDetail(String workId) {
        return workRepository.findById(workId)
            .filter(work -> Boolean.TRUE.equals(work.getVisible()))
            .orElse(null);
    }

    @Transactional
    public WorkEntity createWork(
            String name,
            String description,
            String categoryId,
            String icon,
            String htmlPath,
            Integer order
    ) {
        WorkEntity entity = new WorkEntity();
        entity.setId(UUID.randomUUID().toString());
        entity.setName(name);
        entity.setDescription(description);
        entity.setCategoryId(categoryId);
        entity.setIcon(icon);
        entity.setHtmlPath(htmlPath);
        entity.setOrder(order != null ? order : 0);
        entity.setVisible(true);

        return workRepository.save(entity);
    }

    public static class CategoryWithWorks {
        private final String id;
        private final String name;
        private final String icon;
        private final Integer order;
        private final List<WorkListItem> works;

        public CategoryWithWorks(String id, String name, String icon, Integer order, List<WorkListItem> works) {
            this.id = id;
            this.name = name;
            this.icon = icon;
            this.order = order;
            this.works = works;
        }

        public String getId() { return id; }
        public String getName() { return name; }
        public String getIcon() { return icon; }
        public Integer getOrder() { return order; }
        public List<WorkListItem> getWorks() { return works; }
    }

    public static class WorkListItem {
        private final String id;
        private final String name;
        private final String description;
        private final String icon;
        private final String htmlPath;
        private final Integer order;

        public WorkListItem(String id, String name, String description, String icon, String htmlPath, Integer order) {
            this.id = id;
            this.name = name;
            this.description = description;
            this.icon = icon;
            this.htmlPath = htmlPath;
            this.order = order;
        }

        public String getId() { return id; }
        public String getName() { return name; }
        public String getDescription() { return description; }
        public String getIcon() { return icon; }
        public String getHtmlPath() { return htmlPath; }
        public Integer getOrder() { return order; }
    }
}
