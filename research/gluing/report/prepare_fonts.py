"""Copy locally installed fonts needed to rebuild the report; font binaries are not versioned."""
from pathlib import Path
import shutil

output = Path(__file__).resolve().parent / 'fonts'
names = ['Serif.ttf', 'SerifBold.ttf', 'SerifItalic.ttf', 'SerifBoldItalic.ttf', 'Mono.ttf']
candidates = [
    (Path('/System/Library/Fonts/Supplemental'), [
        'Times New Roman.ttf', 'Times New Roman Bold.ttf', 'Times New Roman Italic.ttf',
        'Times New Roman Bold Italic.ttf', 'Courier New.ttf']),
    (Path('/usr/share/fonts/truetype/liberation2'), [
        'LiberationSerif-Regular.ttf', 'LiberationSerif-Bold.ttf', 'LiberationSerif-Italic.ttf',
        'LiberationSerif-BoldItalic.ttf', 'LiberationMono-Regular.ttf']),
    (Path('/usr/share/fonts/truetype/liberation'), [
        'LiberationSerif-Regular.ttf', 'LiberationSerif-Bold.ttf', 'LiberationSerif-Italic.ttf',
        'LiberationSerif-BoldItalic.ttf', 'LiberationMono-Regular.ttf']),
]
if all((output / name).exists() for name in names):
    print(output)
else:
    for directory, files in candidates:
        if all((directory / file).exists() for file in files):
            output.mkdir(exist_ok=True)
            for source, destination in zip(files, names):
                shutil.copyfile(directory / source, output / destination)
            print(output)
            break
    else:
        raise SystemExit('Install Liberation fonts or put Serif*.ttf and Mono.ttf in report/fonts/.')
