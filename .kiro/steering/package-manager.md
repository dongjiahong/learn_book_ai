# 包管理器规则

在所有项目中，优先使用 yarn 作为包管理器，而不是 npm, npx。

## 具体规则：

- 安装依赖：使用 `yarn add` 而不是 `npm install`
- 安装开发依赖：使用 `yarn add -D` 而不是 `npm install --save-dev`
- 运行脚本：使用 `yarn run` 或直接 `yarn <script>` 而不是 `npm run`
- 全局安装：使用 `yarn global add` 而不是 `npm install -g`
- 删除依赖：使用 `yarn remove` 而不是 `npm uninstall`

## 示例：

```bash
# 安装依赖
yarn add react
yarn add -D typescript

# 运行脚本
yarn dev
yarn build
yarn test

# 删除依赖
yarn remove lodash
```

这个规则适用于所有的项目建议和命令行指令。