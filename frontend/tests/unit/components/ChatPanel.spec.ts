/**
 * ChatPanel组件单元测试
 */
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import ChatPanel from '@/components/ChatPanel.vue';
import type { Message } from '@/types';

describe('ChatPanel', () => {
  it('should render MessageList and ChatInput', () => {
    const wrapper = mount(ChatPanel, {
      props: {
        messages: [],
      },
    });

    expect(wrapper.findComponent({ name: 'MessageList' }).exists()).toBe(true);
    expect(wrapper.findComponent({ name: 'ChatInput' }).exists()).toBe(true);
  });

  it('should pass messages to MessageList', () => {
    const messages: Message[] = [
      {
        message_id: '1',
        session_id: '1',
        role: 'user',
        content: 'Hello',
        created_at: '2024-01-01T12:00:00Z',
      },
    ];

    const wrapper = mount(ChatPanel, {
      props: {
        messages,
      },
    });

    const messageList = wrapper.findComponent({ name: 'MessageList' });
    expect(messageList.props('messages')).toEqual(messages);
  });

  it('should pass streamingContent to MessageList', () => {
    const wrapper = mount(ChatPanel, {
      props: {
        messages: [],
        streamingContent: 'Streaming...',
      },
    });

    const messageList = wrapper.findComponent({ name: 'MessageList' });
    expect(messageList.props('streamingContent')).toBe('Streaming...');
  });

  it('should emit send event when ChatInput sends', async () => {
    const wrapper = mount(ChatPanel, {
      props: {
        messages: [],
      },
    });

    const chatInput = wrapper.findComponent({ name: 'ChatInput' });
    await chatInput.vm.$emit('send', 'Hello');

    expect(wrapper.emitted('send')).toBeTruthy();
    expect(wrapper.emitted('send')?.[0]).toEqual(['Hello']);
  });

  it('should pass disabled to ChatInput', () => {
    const wrapper = mount(ChatPanel, {
      props: {
        messages: [],
        disabled: true,
      },
    });

    const chatInput = wrapper.findComponent({ name: 'ChatInput' });
    expect(chatInput.props('disabled')).toBe(true);
  });

  it('should pass isLoading to ChatInput', () => {
    const wrapper = mount(ChatPanel, {
      props: {
        messages: [],
        isLoading: true,
      },
    });

    const chatInput = wrapper.findComponent({ name: 'ChatInput' });
    expect(chatInput.props('isLoading')).toBe(true);
  });

  it('should expose focusInput method', () => {
    const wrapper = mount(ChatPanel, {
      props: {
        messages: [],
      },
    });

    expect(typeof (wrapper.vm as any).focusInput).toBe('function');
  });

  it('should expose scrollToBottom method', () => {
    const wrapper = mount(ChatPanel, {
      props: {
        messages: [],
      },
    });

    expect(typeof (wrapper.vm as any).scrollToBottom).toBe('function');
  });
});
