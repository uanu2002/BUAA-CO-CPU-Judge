# BUAA CO CPU Judge

[中文](./README.md)

This is inspired by [karin0/buaa-co-cpu-judge](https://github.com/karin0/buaa-co-cpu-judge).

It helps validate a MIPS CPU in Logisim circuit or Verilog HDL based on a given .asm program.

It simplifies the process of manually simulating during debugging.

## Getting Started

### Logisim

Set the output pins in your `main` circuit in the order of PC (default 32-bit), GRF_WRITE_ENABLED (1 bit), GRF_WRITE_ADDRESS (5 bits), GRF_WRITE_DATA (32 bits), DM_WRITE_ENABLED (1 bit), DM_WRITE_ADDRESS (default 32 bits), and DM_WRITE_DATA (32 bits) for the dump instruction to be tested to be automatically loaded into the ROM component.

### Verilog (ISim)

Your test bench should instantiate the CPU and provide a clock. Upon initialization or reset, it should read the instruction memory from `code.txt` using `$readmemh` and write access using `$display`.

## Usage

### Command-Line Interface (CLI)

**In short**, all that is required is to **write MIPS code** and modify the **file paths** for the files in the Examples folder accordingly.

-   Examples/cpu.circ: Circuit under test
-   Examples/std_cpu.circ: Standard/correct circuit
-   Examples/mips1.asm: MIPS code for the test case

#### Logisim

Match the circuit under test with Mars (i.e., step through and compare results)

```
shellCopy Codepython logisim-judge.py Examples/cpu.circ Examples/mips1.asm --dm-address-width 5 --dm-address-by-word
```

Match the circuit under test with the standard circuit

```
shellCopy Codepython logisim-judge.py Examples/cpu.circ --std-circuit-path Examples/std_cpu.circ Examples/mips1.asm --dm-address-width 5 --dm-address-by-word
```

**Results**

Each run will save project files (circuit diagram, machine code, IM image, etc.) in a new folder in the tmp directory (automatically created). Meanwhile, .ans (expected result) and .out (actual result) will be generated in the tmp folder. If the results match (content is consistent), the files are deleted; otherwise, they are kept for analysis. The file content format is as follows:

-   Mars:

    ```
    Copy Code@instruction address: $ register number <= written data
    @00003000: $ 1 <= 00000001
    ```

-   Circuit:

    ```
    Copy Code@instruction machine code: $ register number <= written data
    @34013001: $ 1 <= 00000001
    ```

-   Circuit raw (generated when two circuits are compared; filename.raw.ans and .raw.out):

    ```
    Copy CodePC, GRF_WRITE_ENABLED, GRF_WRITE_ADDRESS, GRF_WRITE_DATA, DM_WRITE_ENABLED, DM_WRITE_ADDRESS, DM_WRITE_DATA
    0011 0100 0000 0001 0000 0000 0000 0001	1	0 0001	0000 0000 0000 0000 0000 0000 0000 0001	0	0 0000	0000 0000 0000 0000 0000 0000 0000 0000
    ```

**Possible Issues**

1.  Due to the different output formats of Mars and circuit, default matching fails. If only the similarity between register operations is compared, you can execute the `Check.sh` script on the command line.

2.  When comparing the circuit with another circuit, all register operations are compared first, followed by all output pins (more comprehensive), and the matching results are output separately.

3.  Standard output for failed matching:

    ```
    Copy Code!! Examples/xxx.asm: InconsistentResults output differs, see xxx xxx ...
    ```

    Standard output for successful matching: blank or

    ```
    Copy Code1/1 xxx.asm ok
    ```

------

------

#### Verilog (ISim)

```
shellCopy CodeshellCopy Code$ python isim-judge.py ise-projects/mips4 tb mips1.asm --recompile
```

Unless the `--recompile` switch is specified, the latest changes on the source may not take effect before manual ISim simulation.

```
shellCopy CodeshellCopy Code$ python isim-judge.py ise-projects/mips5 tb mips1.asm --db
```

The `--db` switch enables delay slot for MARS.

```
shellCopy CodeshellCopy Code$ python isim-judge.py --help
```

### Python APIs

For example utilities, refer to [example.py](https://chatbot.theb.ai/example.py).

#### Example

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

