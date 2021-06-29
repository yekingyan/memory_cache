# memory_cache

内存缓存结果

## 快速开始

```py
@MemoryCache()
def m(i, j=2):
    print("real time")

for _ in range(100):
    r = m(1)

# print("real time") 只会运行一次
```

## 其它

详细用法可看 test.py
