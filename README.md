# BUAA CO CPU Judge

[English](./README_EN.md)

This is inspired by [karin0/buaa-co-cpu-judge](https://github.com/karin0/buaa-co-cpu-judge) .

这有助于根据给定的.asm程序，在Logisim电路或Verilog HDL中对MIPS CPU进行验证。

~~就是简化debug时手动模拟的过程。~~

## 入门指南

### Logisim

按照PC（默认为32位）、GRF_WRITE_ENABLED（1位）、GRF_WRITE_ADDRESS（5位）、GRF_WRITE_DATA（32位）、DM_WRITE_ENABLED（1位）、DM_WRITE_ADDRESS（默认为32位）和DM_WRITE_DATA（32位）的顺序设置您的`main`电路中的输出引脚。要验证的转储指令将自动加载到ROM组件中。

### Verilog（ISim）

您的测试台应该实例化CPU并提供时钟。在初始化或重置时，它应该从`code.txt`中的`$readmemh`读取指令内存，并将访问写入`$display`。

## 用法

### 命令行CLI

**简单来说**，只需要**编写MIPS代码**并将Examples文件夹中文件的**路径修改**为自己的即可。

*   Examples/cpu.circ：待测电路
*   Examples/std_cpu.circ：标准/正确电路
*   Examples/mips1.asm：测试样例的MIPS代码

#### Logisim

将待测电路与Mars对拍（即单步运行并对比结果）

```shell
python logisim-judge.py Examples/cpu.circ Examples/mips1.asm --dm-address-width 5 --dm-address-by-word
```

将待测电路与标准电路对拍

```shell
python logisim-judge.py Examples/cpu.circ --std-circuit-path Examples/std_cpu.circ Examples/mips1.asm --dm-address-width 5 --dm-address-by-word
```

**运行结果**

每次运行都会在tmp文件夹（自动创建）一个新文件夹保存运行过程中的项目文件（电路图、机器码、IM的image等）。同时在tmp文件夹内生成.ans（期望结果）和.out（实际结果），如果对拍成功（内容一致），则删除文件，否则保留分析。文件内容格式如下：

*   Mars：

    ```
    @指令地址: $ 寄存器编号 <= 写入数据
    @00003000: $ 1 <= 00000001
    ```

*   电路：

    ```
    @指令机器码: $ 寄存器编号 <= 写入数据
    @34013001: $ 1 <= 00000001
    ```

*   电路raw（当两电路对比时生成，文件名.raw.ans和.raw.out）：

    ```
    PC、GRF_WRITE_ENABLED GRF_WRITE_ADDRESS GRF_WRITE_DATA DM_WRITE_ENABLED DM_WRITE_ADDRESS DM_WRITE_DATA
    0011 0100 0000 0001 0000 0000 0000 0001	1	0 0001	0000 0000 0000 0000 0000 0000 0000 0001	0	0 0000	0000 0000 0000 0000 0000 0000 0000 0000
    ```

**可能的问题**

1.   由于Mars和电路的输出格式不同，所以默认对拍失败，如果只想比较每次的寄存器操作是否相同，可以在命令行执行`Check.sh`脚本。

2.   电路和电路比较时会先比较所有的寄存器操作，然后再比较所有的输出引脚（更全面），分别输出对拍结果。

3.   对拍失败的标准输出：

     ```
     !! Examples/xxx.asm: InconsistentResults output differs, see xxx xxx ...
     ```

     对拍成功的标准输出：空白或

     ```
     1/1 xxx.asm ok
     ```

     

----

----



#### Verilog（ISim）

```shell
shellCopy Code$ python isim-judge.py ise-projects/mips4 tb mips1.asm --recompile
```

除非指定了开关`--recompile`，否则源上的最新更改可能在手动ISim模拟之前不会生效。

```shell
shellCopy Code$ python isim-judge.py ise-projects/mips5 tb mips1.asm --db
```

开关`--db`为MARS启用了延迟槽

```shell
shellCopy Code$ python isim-judge.py --help
```

### Python APIs

有关实用程序的示例，请参阅[example.py](https://chatbot.theb.ai/example.py)。

#### 示例

```python
from judge import Mars, ISim, Logisim, MarsJudge, DuetJudge, resolve_paths, INFINITE_LOOP

isim = ISim('ise-projects/mips5', 'tb', appendix=INFINITE_LOOP)
mars = Mars(db=True)
judge = MarsJudge(isim, mars)

judge('mips1.asm')
judge.all(['mips1.asm', 'mips2.asm'])
judge.all(resolve_paths('./cases'))
judge.all(resolve_paths(['./cases', './extra-cases', 'mips1.asm']))

logisim = Logisim('mips.circ', 'kits/logisim.jar', appendix=INFINITE_LOOP)
naive_mars = Mars()
judge = MarsJudge(logisim, naive_mars)
judge('mips1.asm')

isim = ISim('ise-projects/mips7', 'tb', appendix=INFINITE_LOOP)
judge = MarsJudge(isim, mars)
judge.load_handler('handler.asm')
judge('exceptions.asm')

std = ISim('ise-projects/mips-std', 'tb', appendix=INFINITE_LOOP)
judge = DuetJudge(isim, std, mars)
judge('interrupts.asm')  # Dui Pai
```

