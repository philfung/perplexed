// Domain-specific apps should replace this file with their parameters.
export const Defaults = {
  appDisplayName: process.env.REACT_APP_DISPLAY_NAME || "perplexed",
  appUserPrompt:
    process.env.REACT_APP_USER_PROMPT || "What do you what to know?",
  searchExamples: [
    {
      emoji: "☕",
      text: "Best coffee shop for taking business meetings in San Francisco.",
    },
    {
      emoji: "🚀",
      text: "What are the latest Disney Marvel movies' theater and streaming release dates?",
    },
    { emoji: "⚽", text: "Who are the best soccer players of all time" },
  ],
};
