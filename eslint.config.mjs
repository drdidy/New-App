import js from "@eslint/js";
import tseslint from "typescript-eslint";
import reactHooks from "eslint-plugin-react-hooks";
import jsxA11y from "eslint-plugin-jsx-a11y";
import nextPlugin from "@next/eslint-plugin-next";

export default [
  {
    ignores: [
      ".next/**",
      "node_modules/**",
      "coverage/**",
      "next-env.d.ts",
      "tsconfig.tsbuildinfo",
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["**/*.{ts,tsx}"],
    plugins: {
      "@next/next": nextPlugin,
      "react-hooks": reactHooks,
      "jsx-a11y": jsxA11y,
    },
    languageOptions: {
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
    },
    rules: {
      ...nextPlugin.configs.recommended.rules,
      ...nextPlugin.configs["core-web-vitals"].rules,
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "warn",
      "jsx-a11y/alt-text": "error",
      "jsx-a11y/aria-props": "error",
      "jsx-a11y/aria-proptypes": "error",
      "jsx-a11y/aria-unsupported-elements": "error",
      "jsx-a11y/role-has-required-aria-props": "error",
      "jsx-a11y/role-supports-aria-props": "error",
      "jsx-a11y/label-has-associated-control": "off",
      "jsx-a11y/no-autofocus": "off",
      "@typescript-eslint/no-explicit-any": "off",
      "@typescript-eslint/no-unused-vars": "off",
      "no-console": ["warn", { allow: ["warn", "error"] }],
      "no-empty": "off",
    },
  },
  {
    files: ["public/sw.js"],
    languageOptions: {
      globals: {
        caches: "readonly",
        clients: "readonly",
        self: "readonly",
        URL: "readonly",
        Promise: "readonly",
        Response: "readonly",
        fetch: "readonly",
      },
    },
  },
];
