/**
 * PreviewPanel组件单元测试
 */
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import PreviewPanel from '@/components/PreviewPanel.vue';
import type { Artifact } from '@/types';

describe('PreviewPanel', () => {
  it('should show empty message when no artifact', () => {
    const wrapper = mount(PreviewPanel, {
      props: {
        artifact: null,
      },
    });

    expect(wrapper.find('[data-testid="preview-empty"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('暂无预览内容');
  });

  it('should render MarkdownPreview for markdown type', () => {
    const artifact: Artifact = {
      type: 'markdown',
      content: '# Hello World',
    };

    const wrapper = mount(PreviewPanel, {
      props: {
        artifact,
      },
    });

    expect(wrapper.find('[data-testid="markdown-preview"]').exists()).toBe(true);
  });

  it('should render HtmlPreview for html type', () => {
    const artifact: Artifact = {
      type: 'html',
      content: '<div>Hello HTML</div>',
    };

    const wrapper = mount(PreviewPanel, {
      props: {
        artifact,
      },
    });

    expect(wrapper.find('[data-testid="html-preview-iframe"]').exists()).toBe(true);
  });

  it('should render SvgPreview for svg type', () => {
    const artifact: Artifact = {
      type: 'svg',
      content: '<svg><circle cx="50" cy="50" r="40" /></svg>',
    };

    const wrapper = mount(PreviewPanel, {
      props: {
        artifact,
      },
    });

    expect(wrapper.find('[data-testid="svg-preview-content"]').exists()).toBe(true);
  });

  it('should render toolbar when artifact exists', () => {
    const artifact: Artifact = {
      type: 'markdown',
      content: '# Test',
    };

    const wrapper = mount(PreviewPanel, {
      props: {
        artifact,
      },
    });

    expect(wrapper.find('[data-testid="preview-toolbar"]').exists()).toBe(true);
  });

  it('should toggle fullscreen when toolbar button clicked', async () => {
    const artifact: Artifact = {
      type: 'markdown',
      content: '# Test',
    };

    const wrapper = mount(PreviewPanel, {
      props: {
        artifact,
      },
    });

    expect(wrapper.find('.preview-panel').classes()).not.toContain('is-fullscreen');

    await wrapper.find('[data-testid="btn-toggle-fullscreen"]').trigger('click');

    expect(wrapper.find('.preview-panel').classes()).toContain('is-fullscreen');
  });
});
