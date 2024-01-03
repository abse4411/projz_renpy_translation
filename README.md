<div align="center">
  <img src="imgs/projz_icon.ico" />
  <br />

[![](https://img.shields.io/badge/projz_renpy_translation-0.4.0-brightgreen.svg)](https://github.com/abse4411/projz_renpy_translation)
[![](https://img.shields.io/badge/license-GPLv3-blue)](https://github.com/abse4411/projz_renpy_translation/blob/devp/LICENSE)

[📘文档（Chinese only）](#快速开始) |
[🛠安装](README_old.md#运行环境准备) |
[💡建议](https://github.com/abse4411/projz_renpy_translation/issues)

简体中文 | [English (N/A)](README_old.md#帮助我们翻译help-us-translate-the-documentation)

</div>

# 开始之前

注意，本工具并不是傻瓜式翻译工具，本工具主要用于管理多个RenPy游戏的翻译项目和机器翻译文本，主要功能如下：
- 无需RenPy SDK即可导入和导出翻译
- 以项目为单位管理RenPy游戏各种语言翻译文本
- 使用免费翻译资源翻译文本
- 翻译文本中潜在错误检查，例如变量，样式标签，转义字符等
- 提供I18n插件注入，为游戏提供语言和字体修改界面

本工具要求您熟悉一定RenPy翻译流程，通过合理利用此工具可以实现快速翻译，并节省大量资源和时间。

对于带有voice语句翻译也是支持的，不过程序默认行为只提取文本语句。
```python
# game/script_21_1320.rpy:8
translate chinese scene_01_5f0ee2360:

    # voice "path/to/file"
    # a "text"
    voice "path/to/file"
    a "translated text"
```
对于上述翻译rpy，只会提取到`a "translated text"`。
如果想要提取`voice "path/to/file"`请在issue提出，这里将给出一份指导。

# ✨新版本V0.4.0

该版本可以支持以下功能：
- 无需RenPy SDK即可生成rpy翻译文件，和原生体验类似
- 可以检测和发现rpy文件中的错误
- 实现游戏注入，可以为RenPy游戏提供语言和字体管理菜单，支持实时生效
- 更简洁，规范的代码，支持实现自定义的翻译接口

现在正在开发中,🚨注意🚨该版本不兼容V0.4.0之前的数据，要使用旧版本请到[这里](https://github.com/abse4411/projz_renpy_translation/tree/9e257770e9b30011b1053da28634c41d958d0fc5)。

# 📈进度

## 已完成：

- Web翻译，仅限google: translate 1 -t web -n google -lang chinese
- AI翻译: translate 1 -t ai -n mbart50 -lang chinese
- 翻译文本潜在错误检查:
  使用`inspect`命令检查已翻译文本中缺失的变量名(如[var])或者样式化标签(如{font})或者转义字符: inspect 1 -l chinese。
  在生成的excel文件完成修复后，使用`updateexcel`命令导入修复的文本：updateexcel 1 -l chinese

## 待完成

- 一些其他命令

# 🛫快速开始

## 1.启动(注意我们使用Python3.8的环境)

```bash
python main.py
```

## 2.创建TranslationIndex

启动后，控制台输入：

```bash
new D:\games\renpy_game_demo -n my_game
```

- `D:\games\renpy_game_demo` 是您的RenPy游戏根目录。
- `-n my_game`是可选的，指定TranslationIndex的别名，因此您可以使用别名代替序号。

> **🚨注意🚨**<br />
> 在运行该命令前，请确保游戏中所有rpa文件被解压(使用[rpatool](https://github.com/Shizmob/rpatool)或
[UnRPA](https://github.com/Lattyware/unrpa))，rpyc转为rpy文件(
> 必须的，不然有些大部分rpy文件无法扫描，使用[unrpyc](https://github.com/CensoredUsername/unrpyc)工具)。
> 或者使用这个集成unrpa和unrypc的工具：[UnRen](https://github.com/VepsrP/UnRen-Gideon-mod-)。

确保以上事项，后输入`ls`命令查看我们创建的TranslationIndex：

```bash
ls
```

输出类似：

```text
Note that: Translation Stats list translated/untranslated lines of dialogue and string for each language.
+-------+---------------+-------------------+------------------+-----------------------------------------------------+
| Index |  Nickname:tag | Translation Stats | Injection state  |                      Game info                      |
+-------+---------------+-------------------+------------------+-----------------------------------------------------+
|   1   |  my_game:None |                   |   Base   True    |       renpy_game_demo-V0.1, Ren'Py 7.4.11.2266      |
|       |               |                   |                  |                D:\games\renpy_game_demo             |
+-------+---------------+-------------------+------------------+-----------------------------------------------------+
```

注意`Injection state`中`Base   True`，这表示我们成功识别并注入该游戏。

## 3.导入一个语言的翻译

启动后，控制台输入：

```bash
import my_game -l schinese
```

- `my_game` 指定导入的TranslationIndex的别名，也可以用索引：1
- `-l schinese` 创建一个名为`schinese`的翻译，
- 这会读取`D:\games\renpy_game_demo\game\tl\schinese`的已经翻译和未翻译的文本

输入`ls`命令查看我们创建的翻译：

```bash
ls
```

输出类似：

```text
Note that: Translation Stats list translated/untranslated lines of dialogue and string for each language.
+-------+---------------+-----------------------------------------+------------------+-----------------------------------------------------+
| Index |  Nickname:tag |            Translation Stats            | Injection state  |                      Game info                      |
+-------+---------------+-----------------------------------------+------------------+-----------------------------------------------------+
|   1   |  my_game:None |   Language   Dialogue   String   Sum    |   Base   True    |       renpy_game_demo-V0.1, Ren'Py 7.4.11.2266      |
|       |               |   schinese    0/940     0/384    1324   |                  |                D:\games\renpy_game_demo             |
+-------+---------------+-----------------------------------------+------------------+-----------------------------------------------------+
```

## 3.使用翻译命令进行翻译

为方便这里使用`savehtml`和`loadhtml`命令进行快速翻译。
Web翻译和AI翻译可用，请查看[帮助](#命令帮助)
，或者参考以前版本的说明：[Web翻译](README_old.md#4使用翻译引擎翻译剩余的文本), [AI翻译](README_old.md#使用dltranslate命令进行ai翻译)。
`saveexcel`, `loadexcel`
命令查看：[使用saveexcel和loadexcel⚡快速⚡翻译](README_old.md#使用saveexcel和loadexcel快速翻译)

现在我们用`savehtml`和`loadhtml`命令来翻译：

```bash
sh 1 -l schinese
```

输出类似：

```text
1320 untranslated lines are saved to ./projz\html\my_game_None_schinese.html.
```

然后使用Chrome或者Microsoft
Edge打开它，右键菜单翻译为指定语言后，Ctrl+S保存该html文件并覆盖原始的`my_game_None_schinese.html`。
这个详细步骤参考[使用savehtml和loadhtml⚡快速⚡翻译（浏览器自带网页翻译）](README_old.md#使用savehtml和loadhtml快速翻译浏览器自带网页翻译)

然后使用`loadhtml`命令导入翻译：

```bash
lh 1 -l schinese
```

输出类似：

```text
...
...
Find 1229 translated lines, and discord 91 lines
schinese: 854 updated dialogue translations, 375 updated string translations. [use:1229, discord:0, total:1229]
```

输入`ls`命令查看我们导入的翻译结果，输出类似：

```text
Note that: Translation Stats list translated/untranslated lines of dialogue and string for each language.
+-------+---------------+-----------------------------------------+------------------+-----------------------------------------------------+
| Index |  Nickname:tag |            Translation Stats            | Injection state  |                      Game info                      |
+-------+---------------+-----------------------------------------+------------------+-----------------------------------------------------+
|   1   |  my_game:None |   Language   Dialogue   String   Sum    |   Base   True    |       renpy_game_demo-V0.1, Ren'Py 7.4.11.2266      |
|       |               |   schinese    856/84    377/7    1324   |                  |                D:\games\renpy_game_demo             |
+-------+---------------+-----------------------------------------+------------------+-----------------------------------------------------+
```

## 4.生成翻译rpy

然后使用`generate`命令来生成翻译rpy文件到游戏：

```bash
generate 1 -l schinese
```

输出类似：

```text
...
...
schinese: dialogue translation: using 856 and missing 84, string translation: using 377 and missing 7
```

需要注意的是，如果`game/tl/{lang}`已经有rpy文件，里面包含翻译文本不会被覆盖，一般`generate`只会添加rpy文件没有的
翻译文本(追加模式)。如果您在TranslationIndex项目中修改了rpy文件已经存在翻译，要把TranslationIndex最新翻译应用
到rpy文件中，请添加`-f`参数，这将删除`game/tl/{lang}`所有rpy/rpyc文件。

## 5.注入我们的I18N插件

在此之前，请手动下载字体文件到`resources/fonts`文件下，下载连接可以在`resources/fonts/readme.txt`找到，
下载完后`resources/fonts`如下内容(请注意字体的版权问题)：

```text
projz_renpy-translator/
    |–– resources/
        –– DejaVuSans.ttf
        –– SourceHanSansLite.ttf
```

使用`inject`命令注入我们提供的I18N插件，其支持修改语言和字体：

```bash
inject 1 -t I18n
```

输入`ls`命令查看注入结果，输出类似：

```text
Note that: Translation Stats list translated/untranslated lines of dialogue and string for each language.
+-------+---------------+-----------------------------------------+------------------+-----------------------------------------------------+
| Index |  Nickname:tag |            Translation Stats            | Injection state  |                      Game info                      |
+-------+---------------+-----------------------------------------+------------------+-----------------------------------------------------+
|   1   |  my_game:None |   Language   Dialogue   String   Sum    |   Base   True    |       renpy_game_demo-V0.1, Ren'Py 7.4.11.2266      |
|       |               |   schinese    856/84    377/7    1324   |   I18n   True    |                D:\games\renpy_game_demo             |
+-------+---------------+-----------------------------------------+------------------+-----------------------------------------------------+
```

您也可以手动启动游戏或者使用`launch`的命令:

```bash
launch 1
```

打开游戏后使用Ctrl+I打开该I18N插件，或者在游戏的设置界面找到名为`I18n settings`的按钮
(按钮的注入需要将screens.rpy文件注入我们的按钮，因此需要把screens.rpyc转为screens.rpy)：
![i18n_button.png](imgs/i18n_button.png)
![i18n.png](imgs/i18n.png)
![i18n.png](imgs/i18n_1.png)

> **💡额外内容💡**<br />
> 你可以在[config.yaml](config.yaml)文件配置生成I18N插件语言设置和字体内容，`inject`命令
> 生成的语言取决于`game/tl`下的非`None`文件夹与[config.yaml](config.yaml)的`lang_map`配置的语言交集，
> 字体可以在[config.yaml](config.yaml)的`fonts`添加。

## 命令帮助

输入`help`命令，打印所有命令的描述和用法，要查看某个命令的所有参数，
请在该命令后面加入一个`-h`选项：

```bash
new -h
```

这将打印`new`命令的详细用法。

> **🍻最后🍻**<br />
> 我们欢迎你集成您的翻译实现到我们的项目中，或者帮助我们翻译文档页面。

# 💪自定义翻译API
如果想要实现自己的翻译API非常简单，在[translator](translator)文件夹下新建一个py文件，然后继承CachedTranslatorTemplate类：
```python
from argparse import ArgumentParser
from translator.base import CachedTranslatorTemplate
from command.translation.base import register
from typing import List, Tuple
from config.base import ProjzConfig

# 翻译API调用流程，以DlTranslator为例：
# 1.用户输入:translate 1 -l chinese -t ai --name mbart50
# 2.创建DlTranslator实例，并调用register_args方法（注意DlTranslator必须使用无参数的构造函数）
# 3.如果用户输入的参数含有'-h'或'--help'，则打印DlTranslator的命令帮助，然后跳转到7.结束。
# 4.调用do_init方法(在这里开始翻译API的初始化应该在这里开始，这里可以使用转换好的args和config)
# 5.调用invoke方法(基类CachedTranslatorTemplate或者TranslatorTemplate已经实现，DlTranslator无需实现)
# 6.根据DlTranslator实现的方法，调用translate_batch或者translate，优先调用translate_batch方法
# 7.结束

class DlTranslator(CachedTranslatorTemplate):
    def register_args(self, parser: ArgumentParser):
      super().register_args(parser)
      # 这里注册您要接受的命令行参数
      # 注意：在这里请不要做任何初始化工作，因为很可能用户只是想知道该翻译API有哪些参数。
      # 初始化工作请放在do_init()方法
      parser.add_argument('-n', '--name', choices=['m2m100', 'mbart50', 'nllb200'], default='mbart50',
                          help='The name of deep learning translation  model.')
        
    def do_init(self, args, config: ProjzConfig):
        super().do_init(args, config)
        # 当用户决定使用这个翻译API时会调用这个方法
        # 请在这里做初始化工作，您现在可以使用已经转换好的args和config
        self._model_name = args.name
        self._model_path = config['translator']['ai']['model_path']
        self._load_model()

    def translate(self, text: str):
        # 您的API翻译方法，接受一个字符串返回一个翻译的字符串
        return self.mt.translate(text, self._source, self._source, batch_size=1, verbose=True)

    def translate_batch(self, texts: List[str]):
        # 如果您的API支持批量翻译，您可以实现该方法。注意返回翻译结果的list长度应该和传入texts的长度一致。
        # 如果没有实现该方法，则会循环调用translate方法。
        return self.mt.translate(texts, self._source, self._source, batch_size=self._batch_size, verbose=True)

# 将您的翻译API注册到translate命令
# 用户可以这样使用：translate 1 -l chinese -t ai --name mbart50
# 其中-t ai为register指定您的翻译API名称
# 注意：DlTranslator应该使用无参数的构造函数，一旦实现无参数的构造函数请记得调用基类构造函数
register('ai', DlTranslator)
```
最后在[translator/__init __.py](translator/__init__.py)导入您的翻译API：
```python
import logging
import translator.base

try:
    import translator.web
except Exception as e:
    print(f'error: {e}')
    logging.exception(e)

try:
    # 您可使用try-except语句导入您的翻译API，这样做可以让用户即使没有安装相应的python库也能正常运行程序。
    # 否者，一旦用户没有相应的python库，将无法运行main.py
    import translator.ai
except Exception as e:
    print(f'error: {e}')
    logging.exception(e)
```
具体示例可以参考[translator/ai/impl.py](translator/ai/impl.py)中`DlTranslator`类的实现。

# 🗒Todo List:

1. [ ] 添加英语文档
2. [ ] GUI支持
3. [ ] 翻译时检查

# 🔗Acknowledgement

我们参考或调用代码：

* 早期项目代码（Web翻译）参考：[Maooookai(Mirage)](https://github.com/Maooookai/WebTranslator), [DrDRR](https://github.com/DrDRR/RenPy-WebTranslator/commits?author=DrDRR "View all commits by DrDRR")
* 使用的AI翻译库：[dl-translate](https://github.com/xhluca/dl-translate)
* 其他使用的python库见：[requirements.txt](./requirements.txt)
