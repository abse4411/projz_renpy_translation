# RenPy翻译文件机翻工具

##### 用于自动生成RenPy翻译文件（*.rpy）的机翻文件。

部分代码来自[Maooookai(Mirage)](https://github.com/Maooookai/WebTranslator), [DrDRR](https://github.com/DrDRR/RenPy-WebTranslator/commits?author=DrDRR "View all commits by DrDRR")，Salute!

## 1.目的

在同一个RenPy游戏中，对于一个已经精翻的rpy文件（比如，来自某个版本V0.28），里面的翻译文本其实在新版本的rpy文件（V0.29）中是可以复用的。因此我们可以先把旧版本可用翻译文本替换到新版本中，然后对于那些没有替换的文本再进行机翻，大大地节省时间。

## 2.流程

本工具分成两个阶段的流程：

1. `incre_parse_.py` 将新版本的rpy文件中可以在旧版rpy文件找到的翻译文本进行进行替换，而对于没有旧版rpy文件没有翻译文本，进行标记，交给下一个阶段进行机翻。此时会生成一个临时版本的rpy文件，其格式按照新版本的rpy，但是如果文本的翻译可以在旧版rpy文件找到，则使用旧版rpy文件的翻译文本，如果找不到对应的翻译文本则对该文本进行特殊标记。

2. `parse_.py`遍历上一个阶段的临时版本的rpy文件，如果某行文本含有特殊标记，则调用翻译API进行翻译，否则保持不变。完成后会生成一个翻译好的rpy文件。

示意图：
![](G:\Xuefeng\Downloads\RenPy-WebTranslator-main\imgs\pipline.jpg)

## 3.运行环境准备

- python 3, 并安装selenium库

- chrome, chrome driver(注意Chrome版本，如果不对请前往 [此链接](https://registry.npmmirror.com/binary.html?path=chromedriver/) 下载对应的chromedriver.exe)

- 科学上网工具(如果使用Google翻译就要用到，现在国内谷歌翻译已经不可用，请使用全局代理模式，保持网络稳定)

## 4.文件准备

1. 把第3节 *3.运行环境准备*  下好chrome driver驱动解压到任意一个目录下，等下要用到。

2. 将旧版本的ryp文件放置到当前代码目录`./old`文件夹下，新版本的ryp文件当前代码目录`./new`文件夹下。放置后的文件目录结构如下（这两个文件夹目录可以通过命令行参数`-o,-n`指定，但是这两个文件夹**必须存在**）：

```
projz/
└── old/
    ├── dayaievents.rpy
    ├── erukaevents.rpy
    └── ...(旧版本rpy，如果没有旧版本rpy可以不放，不影响代码运行)
├── new/
    ├── dayaievents.rpy
    ├── erukaevents.rpy
    └── ...(新版本rpy)
├── file.py
├── incre_parse_.py
├── misc.py
├── parse.py
└── trans_engine.py
```

## 5.运行

### 5.1 第一阶段(旧版本翻译文本复用)

#### 5.1.1 参数说明

`incre_parse_.py`参数如下

```shell
python incre_parse_.py [-o OLD_DIR] [-n NEW_DIR] [-s SAVE]
```

- `-o OLD_DIR`表示第4节 `4.文件准备` 的旧版本的ryp文件目录，默认为`./old`

- `-n NEW_DIR`表示第4节 `4.文件准备` 的新版本的ryp文件目录，默认为`./new`

- `-s SAVE`表示保存临时生成的ryp文件目录，默认为`./tmp`

#### 5.1.2 执行命令

因此，如果如果按第4节 `4.文件准备`放置好ryp文件后，直接运行下面命令就行了：

```shell
python incre_parse_.py
```

上面的命令和下面的命令是等价的：

```shell
python incre_parse_.py -o ./old -n ./new -s ./tmp
```

**注意**：`incre_parse_.py`不会对文件夹进行递归扫描，只扫描一级目录下的rpy文件。

#### 5.1.3 执行效果

执行完毕后，代码目录会多出一个`tmp`文件夹下，里面的rpy文件名和`./new`文件夹的相同：

```
projz/
└── old/
    ├── dayaievents.rpy
    ├── erukaevents.rpy
    └── ...(旧版本rpy，如果没有旧版本rpy可以不放，不影响代码运行)
├── new/
    ├── dayaievents.rpy
    ├── erukaevents.rpy
    └── ...(新版本rpy)
├── tmp/
    ├── dayaievents.rpy
    ├── erukaevents.rpy
    └── ...(临时rpy，包含来自旧版本翻译和未翻译的文本)
├── file.py
├── incre_parse_.py
├── misc.py
├── parse.py
├── tran_summary.txt
└── trans_engine.py
```

同时，还会代码目录下生成一个`tran_summary.txt`文件，统计每个文件中复用旧版本的rpy文件翻译的行数和需要机翻行数，文件内容类似下面：

> 2023-03-31 12:44:57 \
> dayaievents.rpy[total line(s):2967] is translated with 2937 translated line(s) and 30 untranslated line(s). \
> erukaevents.rpy[total line(s):18315] is translated with 18082 translated line(s) and 233 untranslated line(s). \
> dreamevents.rpy[total line(s):1164] is translated with 1007 translated line(s) and 157 untranslated line(s). \
> 3 rpy files are translated with 22026 translated line(s) and 420 untranslated line(s). 

然后我们就可以知道，我们复用多少行翻译和需要翻译多少行。

#### 5.1.4 代码原理

在旧版本rpy中，例如：

>         # renpy/common/00accessibility.rpy:33
>         old "selected"
>         new "选择"
>     
>         # game/ImaniEvents.rpy:11
>     translate chinese callimanimorning_88744462:
>     
>         # "She doesn’t pick up."
>         "她没有接听。"

我们可以把`old "selected"`中的原始文本`selected`当成字典的key，而`new "选择"`中的翻译文本`选择`当成字典的value，这样就可以得到一个原始文本到翻译文本的映射（`"selected"->"选择"`），因此我们在旧版本rpy文件就是如何识别原始文本和翻译文本，然后构建这个翻译字典即可。

对于新的rpy文件我们只要做的是提取原始文本然后用翻译字典中有进行替换就行了。注意，我们使用renpy SDK生成翻译文件时候需要保留原始文本，不要勾选未翻译生成空字符串的选项：

![](G:\Xuefeng\Downloads\RenPy-WebTranslator-main\imgs\renpy.png)

之后生成的ryp文件应该是这样的：

>     # game/ImaniEvents.rpy:11
>     translate chinese callimanimorning_88744462:
>     
>         # "She doesn’t pick up."
>         "She doesn’t pick up."

只有这样格式的ryp，才能代码才可以识别原始文本然后进行替换。注意有的旧的翻译ryp文件可能会把末尾的`"`给弄没了，变成这样（文本`# "She doesn’t pick up.`后面少了一个引号）：

> ```
> # game/ImaniEvents.rpy:11
> translate chinese callimanimorning_88744462:
> 
>     # "She doesn’t pick up.
>     "她没有接听。"
> ```

这种ryp文件需要手动加上在末尾加上引号，才能进行处理，否则代码会报不匹配异常（可以看到在哪一行出了问题），后续会上传该校正这种错误的代码（`correct_rawtext.py`）。我们匹配规则是：`# "She doesn’t pick up"`（代码中对应raw_text）对应`"她没有接听。"`（代码中对应new_text），且这两行必须相邻的。

如果翻译字典不存在的这段翻译的文本，我们为这个文本开头加上特殊标记`@$`表示这段文本需要进行翻译：

> ```
> # game/ImaniEvents.rpy:11
> translate chinese callimanimorning_88744462:
> 
>     # "She doesn’t pick up."
>     "@$She doesn’t pick up."
> 
> # game/diceevents.rpy:40
> translate chinese diceevent1_064b67cc:
> 
>     # dic "..."
>     dic "..."
> ```

第二阶段就是把这些特殊标记的文本进行机翻。此外,对于一些没有需要翻译内容的文本（如没有字母的文本）也不会添加特殊标记，如上面的`dic "..."`。

### 5.2 第二阶段(机翻特殊标记文本)

#### 5.2.1 参数说明

`incre_parse_.py`参数如下

```shell
python parse.py FILENAME/DIRNAME --driver DRIVER [-t API_NAME] [-s SAVE]
```

- `FILENAME/DIRNAME`表示要进行机翻的rpy目录或者rpy文件路径，不会递归扫描文件。
  
  例如：
  
  ```
  python parse.py ./tmp a.rpy ./my_typs
  ```

- `--driver DRIVER`表示第3节 `4.文件准备` 中解压好的chrom edriver文件的路径，例如：

```
--driver "G:\Admin\Downloads\chromedriver_win32\chromedriver.exe"
```

如果觉得每次都要指定很麻烦，请在`incre_parse_.py`设置该参数的默认值：

```python
parser.add_argument(
    "--driver",
    type=str,
    default=r"G:\Admin\Downloads\chromedriver_win32\chromedriver.exer"
    required=True,
    help="the executable path for the chrome driver",
)
```

- `-t API_NAME`表示使用翻译API，默认为`google`，可选的有：`['caiyun', 'youdao', 'deepl', 'google']`，建议使用google翻译，对于文本的中字符格式化标签能保留下来，即"{i}Hello world{/i}"翻译后”{i}你好世界{/i}“。对于其他翻译API我在翻译前手动去除了这些标签：

```python
def translate(self, rawtext):
    res = strip_breaks(rawtext) # 去除换行符，和文本头尾的空白字符
    res = strip_tags(res)  # 去除字符格式化标签
```

`-s SAVE`表示保存机翻ryp文件目录，默认为`./translated`。如果`FILENAME/DIRNAME`参数含有文件夹，则会在`./translated`目录生成一个同名的文件夹，然后保存机翻的rpy文件到这个同名的文件夹里面；如果`FILENAME/DIRNAME`参数含文件，则直接在`./translated``生成同名的机翻的rpy文件。

#### 5.2.2 执行命令

我们指定第一阶段保存临时rpy文件的目录`./tmp`为我们要机翻的目录，同时指定chrome驱动文件位置:

```shell
python parse.py ./tmp --driver "G:\Admin\Downloads\chromedriver_win32\chromedriver.exe"
```

#### 5.2.3 执行效果

![](G:\Xuefeng\Downloads\RenPy-WebTranslator-main\imgs\stage2.jpg)

执行完毕后，代码目录会多出一个`tmp`文件夹下，里面的rpy文件名和`./new`文件夹的相同：

```
projz/
├── old/
    ├── dayaievents.rpy
    ├── erukaevents.rpy
    └── ...(旧版本rpy，如果没有旧版本rpy可以不放，不影响代码运行)
├── new/
    ├── dayaievents.rpy
    ├── erukaevents.rpy
    └── ...(新版本rpy)
├── tmp/
    ├── dayaievents.rpy
    ├── erukaevents.rpy
    └── ...(临时rpy，包含来自旧版本翻译和未翻译的文本)
├── translated/
    └── tmp/
        ├── dayaievents.rpy
        ├── erukaevents.rpy
        └── ...(机翻rpy)
├── file.py
├── incre_parse_.py
├── misc.py
├── parse.py
├── tran_summary.txt
└── trans_engine.py
```

#### 5.1.4 代码原理

扫描第一阶段的临时rpy文件（例如下面），提取含有特殊标记`@$`文本调用翻译API进行翻译。

> ```
> # game/ImaniEvents.rpy:11
> translate chinese callimanimorning_88744462:
> 
>     # "She doesn’t pick up."
>     "@$She doesn’t pick up."
> 
> # game/diceevents.rpy:40
> translate chinese diceevent1_064b67cc:
> 
>     # dic "..."
>     dic "..."
> ```

- 由于调用翻译API过程中可能出错导致文本没有被翻译到，还需要进行翻译，我们仍保留特殊标记，事后可以自己进行翻译（Ctrl + F 查找这个特殊标记`@$`），或者把在`./translated`目录下对应的ryp文件剪切到第一阶段的`./tmp`目录下就行（替换临时对应ryp），重新执行代码即可，注意`./translated`目录下对应的ryp文件要删掉（由于检查点机制的存在）。

- 第二阶段翻译代码具有检查点的机制，也就是说：当`./tmp`某个文件翻译一半时候，程序寄了，导致`./translated`目录下对应机翻rpy文件部分内容缺失，则第二阶段代码下次重新运行的时候会从上次这个rpy文件中断的行（对比`./translated`目录下对应的rpy文件）继续翻译。

- 此外，由于这个检查点的机制存在，如果整个翻译完的文件则不会进行重复翻译。因此`./translated`目录下内容完整的rpy文件（行数和`./tmp`对应的rpy文件一样），不会进行重复翻译。

- 对于存在变量名的的文本，例如，待翻译的文本为：
  
  ```
  I love you, [player].
  ```
  
   送入翻译API前，会把`[player]`替换为`T0V`:
  
  ```
  I love you, T0V.
  ```
  
   替换后再送入翻译API后，再把翻译结果的`T0V`替换为`[player]`:
  
  ```
  我爱你, [player].
  ```

- 对于存在字符格式标签的文本，如果使用非Google翻译API会把标签去除（Google翻译带标签的文本后仍会保留标签，因此翻译前不用去除标签），原始本文：
  
  ```
  <i> I love you </i>
  ```
  
  去除后：
  
  ```
    I love you 
  ```
  
  然后再送入翻译API中。这做是因为非Google翻译API会把字符格式标签给翻译了，导致运行游戏时候报错。如果标签只出现文本的头尾，那么是可以翻译后重新加上去的，但是代码没有这样做（懒）。

## 6.自定义翻译引擎API

在`trans_engine.py`创建一个类，并继承抽象类`translator`即可，然后重写里面的`translate`方法。

```python
# Abstract translator
class translator:

    def translate(self, rawtext):
        return rawtext


class mytransapi(translator):
    def __init__(self, browser):
        self.browser = browser
        # Your code here

    def translate(self, rawtext):
        # Your code here
```

然后在`parse.py`文件，为命令行参数`-t` 添加这个自定义类的类名到choices列表里即可：

```python
parser.add_argument(
    "-t",
    "--trans_api",
    type=str,
    default='google',
    choices=['caiyun', 'youdao', 'deepl', 'google', 'mytransapi'],
    help="the translation API to use",
)
```

## 其他问题

- 虽然在 `5.1.4 代码原理` 说过Google翻译可以翻译带标签的文本，但是标签如果有参数之类的可能会在标签加空格导致代码出错。因此，如果想要去除标签，在`trans_engine.py`代码中的`google`类的`translate`方法调用`strip_tags(res)`即可：
  
  ```python
  def translate(self, rawtext):
        res = strip_breaks(rawtext)
        res = strip_tags(res)  # 加上这个
  ```

## Todo

1. 翻译API的translate实现对于获取翻译结果判断可能有问题（过长文本的翻译结果可能缺失），由于个人时间和能力有限，需要进一步完善，例如优化获取翻译结果逻辑，减少睡眠时间来提高翻译效率。
2. 由于翻译网站可能发生变化，原有代码可能不能使用，需要进行适配。欢迎XDM对代码进行贡献。
3. 视频演示？Emmmm......
