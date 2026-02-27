/**
 * MessageList组件单元测试
 */
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import MessageList from '@/components/chat/MessageList.vue';
import type { Message } from '@/types';

describe('MessageList', () => {
  it('should render list of messages', () => {
    const messages: Message[] = [
      {
        id: 1,
        session_id: 1,
        role: 'user',
        content: 'Hello',
        created_at: '2024-01-01T12:00:00Z',
      },
      {
        id: 2,
        session_id: 1,
        role: 'assistant',
        content: 'Hi there!',
        created_at: '2024-01-01T12:00:01Z',
      },
    ];

    const wrapper = mount(MessageList, {
      props: {
        messages,
      },
    });

    const messageItems = wrapper.findAll('[data-testid="message-item"]');
    expect(messageItems.length).toBe(2);
  });

  it('should render streaming message when content provided', () => {
    const wrapper = mount(MessageList, {
      props: {
        messages: [],
        streamingContent: 'Streaming...',
      },
    });

    expect(wrapper.find('[data-testid="streaming-message-wrapper"]').exists()).toBe(true);
  });

  it('should not render streaming message when no content', () => {
    const wrapper = mount(MessageList, {
      props: {
        messages: [],
        streamingContent: '',
      },
    });

    expect(wrapper.find('[data-testid="streaming-message-wrapper"]').exists()).toBe(false);
  });

  it('should expose scrollToBottom method', () => {
    const wrapper = mount(MessageList, {
      props: {
        messages: [],
      },
    });

    expect(typeof (wrapper.vm as any).scrollToBottom).toBe('function');
  });
});
