/**
 * MessageItem组件单元测试
 */
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import MessageItem from '@/components/chat/MessageItem.vue';
import type { Message } from '@/types';

describe('MessageItem', () => {
  it('should render user message correctly', () => {
    const message: Message = {
      id: 1,
      session_id: 1,
      role: 'user',
      content: 'Hello AI',
      created_at: '2024-01-01T12:00:00Z',
    };

    const wrapper = mount(MessageItem, {
      props: {
        message,
      },
    });

    expect(wrapper.find('.message-user').exists()).toBe(true);
    expect(wrapper.text()).toContain('Hello AI');
  });

  it('should render assistant message correctly', () => {
    const message: Message = {
      id: 2,
      session_id: 1,
      role: 'assistant',
      content: 'Hello User',
      created_at: '2024-01-01T12:00:00Z',
    };

    const wrapper = mount(MessageItem, {
      props: {
        message,
      },
    });

    expect(wrapper.find('.message-assistant').exists()).toBe(true);
    expect(wrapper.text()).toContain('Hello User');
  });

  it('should render markdown for assistant message', () => {
    const message: Message = {
      id: 1,
      session_id: 1,
      role: 'assistant',
      content: '# Heading',
      created_at: '2024-01-01T12:00:00Z',
    };

    const wrapper = mount(MessageItem, {
      props: {
        message,
      },
    });

    const html = wrapper.find('[data-testid="message-text"]').html();
    expect(html).toContain('<h1>');
  });

  it('should not render markdown for user message', () => {
    const message: Message = {
      id: 1,
      session_id: 1,
      role: 'user',
      content: '# Heading',
      created_at: '2024-01-01T12:00:00Z',
    };

    const wrapper = mount(MessageItem, {
      props: {
        message,
      },
    });

    const html = wrapper.find('[data-testid="message-text"]').html();
    // 用户消息不应该被渲染为markdown
    expect(html).not.toContain('<h1>');
    expect(wrapper.text()).toContain('# Heading');
  });

  it('should format timestamp', () => {
    const message: Message = {
      id: 1,
      session_id: 1,
      role: 'user',
      content: 'Test',
      created_at: '2024-01-01T14:30:00Z',
    };

    const wrapper = mount(MessageItem, {
      props: {
        message,
      },
    });

    const timeElement = wrapper.find('[data-testid="message-time"]');
    expect(timeElement.exists()).toBe(true);
    expect(timeElement.text()).toMatch(/\d{2}:\d{2}/);
  });

  it('should display correct avatar for user', () => {
    const message: Message = {
      id: 1,
      session_id: 1,
      role: 'user',
      content: 'Test',
      created_at: '2024-01-01T12:00:00Z',
    };

    const wrapper = mount(MessageItem, {
      props: {
        message,
      },
    });

    const avatar = wrapper.find('.avatar-image');
    expect(avatar.attributes('src')).toContain('user-avatar');
  });

  it('should display correct avatar for assistant', () => {
    const message: Message = {
      id: 1,
      session_id: 1,
      role: 'assistant',
      content: 'Test',
      created_at: '2024-01-01T12:00:00Z',
    };

    const wrapper = mount(MessageItem, {
      props: {
        message,
      },
    });

    const avatar = wrapper.find('.avatar-image');
    expect(avatar.attributes('src')).toContain('ai-avatar');
  });
});
