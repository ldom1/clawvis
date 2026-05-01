import { createApp } from "./app.js";

const app = createApp();
const port = process.env.PORT || 3000;

app.listen(port, () => {
  console.log(`{{PROJECT_NAME}} running on :${port}`);
});
