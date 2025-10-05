import { Composio } from '@composio/core';
import { generateText, ModelMessage, stepCountIs, streamText } from 'ai';
import { openai } from '@ai-sdk/openai';
import { VercelProvider } from '@composio/vercel';
import dotenv from 'dotenv';
import { MessageRoles } from './types';
dotenv.config();

/**
 * Initialize the Composio SDK with the Vercel provider
 */
const composio = new Composio({
  apiKey: process.env.COMPOSIO_API_KEY,
  provider: new VercelProvider(),
});

/**
 * Get the hacker news tool
 * Alternatively, you can use the `composio.getToolBySlug` method
 */
async function run() {
  const tools = await composio.tools.get('test-user-id', 'HACKERNEWS_GET_FRONTPAGE', {
    beforeExecute: ({ params, toolSlug }) => {
      console.log(`🔄 Executing ${toolSlug} with params:`, { params });
      return params;
    },
    afterExecute: ({ result, toolSlug }) => {
      console.log(`✅ Executed ${toolSlug} with result:`);
      return result;
    },
  });

  const messages: ModelMessage[] = [
    {
      role: MessageRoles.USER,
      content: 'Summarize the front page of HackerNews',
    },
  ];

  const stream = await streamText({
    model: openai('gpt-4o-mini'),
    tools: tools,
    messages,
    stopWhen: stepCountIs(5),
  });

  for await (const textPart of stream.textStream) {
    process.stdout.write(textPart);
  }
}

run();
