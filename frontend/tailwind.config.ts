import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        cda: {
          navy: "#09264B",
          blue: "#006DAE",
          coral: "#F26A48",
          mint: "#7DBCB1",
          gold: "#F2C97A",
        },
      },
    },
  },
  plugins: [],
};
export default config;
