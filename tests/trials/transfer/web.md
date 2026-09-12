防抖只能减少请求次数，**不能保证已经发出的请求按发送顺序完成，也不能决定哪个响应还能更新页面**。

假设防抖时间是 300 毫秒，下面的顺序仍然可能发生：

| 时刻 | 发生的事 |
|---|---|
| 0 ms | 输入 `ca` |
| 300 ms | 停顿足够久，发出 `ca` 请求 |
| 400 ms | 输入变成 `cat`，重新计时 |
| 700 ms | 发出 `cat` 请求 |
| 800 ms | `cat` 响应完成，显示 `cat` 结果 |
| 1000 ms | `ca` 响应完成，覆盖成 `ca` 结果 |

防抖在这段过程里正常工作了。第二次输入只能清除尚未执行的定时器，先前那个定时器已经发出了请求，清除它不会撤回请求。

你已经懂 Promise，可以把两个请求看作两条独立的 Promise 链：哪条先完成，哪条的后续代码先有机会执行。如果每条链最后都无条件调用 `renderResults(data)`，晚完成的就会覆盖先完成的。把 `.then()` 改成 `await` 也一样：每次调用只等待自己的请求，不会让不同调用自动排队。

需要补上的规则是：**结果写入页面前，检查它是否仍对应最新一次输入。** 可以给每次输入递增一个版本号，每个请求记住发起它的版本。

下面是浏览器端普通 JavaScript 的核心代码。假设页面已有 `input#search`，接口返回 JSON 数组；`renderResults`、`showStatus` 是你已有的同步界面更新函数，分别负责结果列表和提示文字。

```js
const input = document.querySelector("#search");
let timer;
let inputVersion = 0;

input.addEventListener("input", () => {
  const myVersion = ++inputVersion;
  const q = input.value.trim();
  clearTimeout(timer);

  renderResults([]);
  showStatus(q ? "等待输入完成…" : "");
  if (!q) return;

  timer = setTimeout(async () => {
    if (myVersion !== inputVersion) return;
    showStatus("搜索中…");

    try {
      const response = await fetch(
        `/api/search?q=${encodeURIComponent(q)}`
      );
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();

      // 请求与正文读取都结束后，再决定能否写入页面。
      if (myVersion !== inputVersion) return;
      renderResults(data);
      showStatus(data.length ? "" : "没有匹配结果");
    } catch (error) {
      if (myVersion !== inputVersion) return;
      console.error("搜索失败", { q, myVersion, error });
      showStatus("搜索失败，请重试");
    }
  }, 300);
});
```

这里 `ca` 请求记住版本 1，输入 `cat` 后全局版本变成 2。无论版本 1 的响应何时完成，都不能再更新界面；版本 1 的错误也不能把版本 2 的结果换成错误提示。

版本号要在**输入变化时立即递增**。如果等到新请求真正发出才递增，那么输入已是 `cat`、但还在等待防抖的 300 毫秒里，旧 `ca` 响应仍会被误认为有效。代码在 `response.json()` 之后检查，是因为读取正文也需要异步等待；`response.ok` 则用于识别不会自动让 `fetch` 拒绝的 HTTP 错误。[MDN Fetch 指南](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)

还可以在新输入到来时用 `AbortController` 取消旧请求，减少不再需要的传输和处理。但取消不会撤销已经执行的界面更新，因此仍应把版本检查放在最终写入处。[MDN 请求取消说明](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch#canceling_a_request)

观察时，在浏览器 Network 面板看两个请求的完成顺序，并在版本检查前打印 `q、myVersion、inputVersion`。预期是：即使 `ca` 最后回来，页面仍保留 `cat` 的结果，因为旧响应到达了，却没有获得更新页面的资格。
