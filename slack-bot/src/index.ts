import pkg from '@slack/bolt';
const { App } = pkg;
import * as dotenv from 'dotenv';
import axios from 'axios';

dotenv.config();

const app = new App({
  token: process.env.SLACK_BOT_TOKEN || '',
  signingSecret: process.env.SLACK_SIGNING_SECRET || '',
  socketMode: true, // Enable socket mode for local development
  appToken: process.env.SLACK_APP_TOKEN || '',
});

// Listen for direct messages to the bot
app.message(async ({ message, say }) => {
  // @ts-ignore
  if (message.channel_type === 'im') {
    await say("Je réfléchis à ta question...");
    // @ts-ignore
    const userMessage = message.text;
    // @ts-ignore
    const {data: {status, answer}} = await axios.post(`${process.env.API_URL}/ask`, { question: userMessage, debug: true, context_type: "auto" })

    if (status !== 'success') {
      await say("Désolé, je n'ai pas pu traiter ta question.");
      return;
    }
   
    await say(answer);
  }
});

// Listen for messages mentioning the bot in channels
app.event('app_mention', async ({ event, say }) => {
  // Extract the question by removing the bot mention
  const question = event.text.replace(/<@[A-Z0-9]+>/g, '').trim();
  
  console.log(`Question from user ${event.user} in channel: ${question}`);
  
  // Reply in a thread
  await say({
    text: `You asked: "${question}"\n\nI'm processing your question... (This is where you'd generate an answer)`,
    thread_ts: event.ts, // Reply in thread
  });
});


// Start the app
(async () => {
  await app.start();
  console.log('⚡️ Slack bot is running!');
})();