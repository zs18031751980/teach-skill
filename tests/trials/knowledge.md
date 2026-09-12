`reverse=True` 改变的是**排序方向**：让 `sorted` 按与默认排序相反的方向排列元素。对于数字，默认从小到大，设为 `True` 后从大到小。

```python
items = [3, 1, 2]
sorted(items)                # [1, 2, 3]
sorted(items, reverse=True)  # [3, 2, 1]
```

它仍然会先按元素的大小关系排序，不是直接把原列表倒过来；上面的原列表直接倒序会是 `[2, 1, 3]`。`sorted` 返回新列表，`items` 本身不变。
