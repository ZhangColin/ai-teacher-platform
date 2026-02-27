/**
 * HtmlPreview组件单元测试
 */
import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import HtmlPreview from '@/components/preview/HtmlPreview.vue';

// Mock DOMPurify
vi.mock('dompurify', () => ({
  default: {
    sanitize: (html: string, config: any) => {
      // 简单模拟DOMPurify的清理行为：移除script标签
      return html.replace(/<script\b[^>]*>([\s\S]*?)<\/script>/gim, '');
    },
  },
}));

describe('HtmlPreview', () => {
  it('should render iframe with sanitized HTML', () => {
    const wrapper = mount(HtmlPreview, {
      props: {
        content: '<div>Hello HTML</div>',
      },
    });

    const iframe = wrapper.find('[data-testid="html-preview-iframe"]');
    expect(iframe.exists()).toBe(true);
    expect(iframe.attributes('srcdoc')).toBe('<div>Hello HTML</div>');
  });

  it('should show empty message when content is empty', () => {
    const wrapper = mount(HtmlPreview, {
      props: {
        content: '',
      },
    });

    expect(wrapper.find('[data-testid="html-preview-iframe"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="html-preview-empty"]').exists()).toBe(true);
    expect(wrapper.text()).toContain('No HTML content');
  });

  it('should sanitize HTML content', () => {
    const content = '<div><script>alert("xss")</script>Hello</div>';

    const wrapper = mount(HtmlPreview, {
      props: {
        content,
      },
    });

    const srcdoc = wrapper.find('[data-testid="html-preview-iframe"]').attributes('srcdoc');
    // DOMPurify应该移除script标签
    expect(srcdoc).not.toContain('<script>');
  });

  it('should set sandbox attribute on iframe', () => {
    const wrapper = mount(HtmlPreview, {
      props: {
        content: '<div>Test</div>',
      },
    });

    const iframe = wrapper.find('[data-testid="html-preview-iframe"]');
    expect(iframe.attributes('sandbox')).toBe('allow-scripts allow-same-origin');
  });
});
