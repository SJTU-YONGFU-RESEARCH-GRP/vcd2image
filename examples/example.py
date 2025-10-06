#!/usr/bin/env python
"""Examples of using the vcd2image package."""

from vcd2image.core.extractor import WaveExtractor
from vcd2image.core.multi_renderer import MultiFigureRenderer


def example1():
    """Check the path name of the signal in the VCD file."""

    extractor = WaveExtractor('examples/timer.vcd', '', [])
    extractor.print_props()


if __name__ == '__main__':
    print('')
    print('Example 1')
    print('----------------------------------------')
    example1()

    # Example 1
    # ----------------------------------------
    # vcd_file  = 'timer.vcd'
    # json_file = ''
    # path_list = ['tb_timer/clock',
    #              'tb_timer/pulse',
    #              'tb_timer/reset',
    #              'tb_timer/u_timer/clock',
    #              'tb_timer/u_timer/count',
    #              'tb_timer/u_timer/count_eq11',
    #              'tb_timer/u_timer/pulse',
    #              'tb_timer/u_timer/reset']
    # wave_chunk = 20
    # start_time = 0
    # end_time   = 0


def example2():
    """Extract the signal values specified in the path list
       and output WaveJSON string to the file."""

    path_list = ['tb_timer/u_timer/clock',
                 'tb_timer/u_timer/reset',
                 'tb_timer/u_timer/pulse',
                 'tb_timer/u_timer/count_eq11',
                 'tb_timer/u_timer/count']

    extractor = WaveExtractor('examples/timer.vcd', 'examples/timer.json', path_list)
    extractor.execute()


if __name__ == '__main__':
    print('')
    print('')
    print('Example 2')
    print('----------------------------------------')
    example2()

    # Example 2
    # ----------------------------------------
    # vcd_file  = 'timer.vcd'
    # json_file = 'timer.json'
    # path_list = ['tb_timer/u_timer/clock',
    #              'tb_timer/u_timer/reset',
    #              'tb_timer/u_timer/pulse',
    #              'tb_timer/u_timer/count_eq11',
    #              'tb_timer/u_timer/count']
    # wave_chunk = 20
    # start_time = 0
    # end_time   = 0
    #
    # Create WaveJSON file "timer.json".


def example3():
    """Set sampling duration and display format.
       The result is displayed on standard output."""

    path_list = ['tb_timer/u_timer/clock',
                 'tb_timer/u_timer/reset',
                 'tb_timer/u_timer/pulse',
                 'tb_timer/u_timer/count_eq11',
                 'tb_timer/u_timer/count']

    extractor = WaveExtractor('examples/timer.vcd', '', path_list)
    extractor.wave_chunk = 10
    extractor.start_time = 100
    extractor.end_time = 500
    extractor.wave_format('tb_timer/u_timer/count', 'u')
    extractor.execute()


if __name__ == '__main__':
    print('')
    print('')
    print('Example 3')
    print('----------------------------------------')
    example3()

    # Example 3
    # ----------------------------------------
    # { "head": {"tock":1},
    #   "signal": [
    #   {   "name": "clock"     , "wave": "p........." },
    #   {},
    #   ["110",
    #     { "name": "reset"     , "wave": "1...0....." },
    #     { "name": "pulse"     , "wave": "x0........" },
    #     { "name": "count_eq11", "wave": "0........." },
    #     { "name": "count"     , "wave": "=....=====", "data": "0 1 2 3 4 5" }
    #   ],
    #   {},
    #   ["310",
    #     { "name": "reset"     , "wave": "0........." },
    #     { "name": "pulse"     , "wave": "0.....10.." },
    #     { "name": "count_eq11", "wave": "0....10..." },
    #     { "name": "count"     , "wave": "==========", "data": "6 7 8 9 10 11 0 1 2 3" }
    #   ]
    #   ]
    # }


def example4():
    """Auto plotting: Generate single organized plot with all signals."""

    renderer = MultiFigureRenderer()
    renderer.render_lazy_plot('examples/timer.vcd', 'examples/timer_auto.png')


if __name__ == '__main__':
    print('')
    print('')
    print('Example 4')
    print('----------------------------------------')
    example4()

    # Example 4
    # ----------------------------------------
    # Generates timer_auto.png with all signals organized in a single figure


def example5():
    """Auto plotting: Generate multiple categorized figures."""

    renderer = MultiFigureRenderer()
    renderer.render_categorized_figures(
        vcd_file='examples/timer.vcd',
        output_dir='examples/figures',
        base_name='timer',
        formats=['png', 'svg', 'html']
    )


if __name__ == '__main__':
    print('')
    print('')
    print('Example 5')
    print('----------------------------------------')
    example5()

    # Example 5
    # ----------------------------------------
    # Generates multiple figures:
    # - timer_ports.png/svg/html: Input and output ports
    # - timer_internal.png/svg/html: Internal signals
    # - timer_all.png/svg/html: All signals
