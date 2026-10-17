# 维护课程练习

本仓库采用 [Rustlings 社区练习格式](https://rustlings.rust-lang.org/community-exercises/)，使用独立安装的官方 Rustlings 6.5.0 或更新版本。

## 修改练习

题目在 `exercises/<主题>/<题目名>.rs` 中；每个题目都需要 `fn main()`，只有测试的题目可使用空的 `fn main() {}`。修改已有题目时保留测试意图，不要将答案写进题目模板。

题目顺序、提示和运行方式由 `info.toml` 决定：

```toml
[[exercises]]
name = "example1"
dir = "example"
test = true
strict_clippy = false
hint = "本题提示"
```

`test` 默认为 `true`；纯编译运行题设置为 `false`。`strict_clippy` 默认为 `false`，Clippy 题设置为 `true`。Rustlings 会对每道题运行 Clippy。

修改清单后执行：

```sh
rustlings dev update
python3 -m unittest discover -s .github/tests -v
```

`Cargo.toml` 的 `bin` 列表由更新命令生成。其余 Cargo 配置可手动维护。编辑器通过 Cargo 识别练习。

`rustlings dev check` 面向题目模板作者，会要求题目尚未解答以及每题包含 TODO；已经做过题目的学生仓库不应把它作为验收命令。

## 评分兼容性

课程的 110 题、题目路径、顺序和分值由 `course.json` 固定，题目仅使用 Rust 标准库。`.github/scripts/grade.py` 会校验新版题目清单和 Cargo targets 与课程规则一致，再为每题建立临时 Cargo 包，依次编译、测试、检查 Clippy 和运行程序。每题的所有步骤共用 20 秒限时，仍按题计分。

`tests7` 和 `tests8` 共用 `exercises/tests/build.rs`。交互工具将它作为练习包的构建脚本；其中的重新执行设置用于让时间戳测试在使用缓存时仍然有效。评分时仅这两题挂载该脚本，避免脚本语法错误导致其他题目失分。不要删除它，也不要将对应题目的答案移到其他配置文件。

本地完整评分（不会上传成绩）：

```sh
python3 .github/scripts/grade.py
```

评分结果和各题日志写入 `tmp/grade/`。GitHub Actions 负责独立的成绩上传流程。
