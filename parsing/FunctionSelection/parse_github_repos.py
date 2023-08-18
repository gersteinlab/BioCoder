"""
The purpose of the file is to automate the parsing of repositories by 
calling parse.py for each repository
"""

import subprocess
import os
from tqdm import tqdm

repo_directory_dict = [
    ['aTRAM', 'juliema'],
    ['CellProfiler/cellprofiler', 'CellProfiler'],
    ['cnvkit/cnvlib', 'etal'],
    ['cnvkit/skgenome', 'etal'],
    ['deblur/deblur', 'biocore'],
    ['DNApi', 'jnktsj'],
    ['Dynamics', 'makson96'],
    ['ensembler/ensembler', 'choderalab'],
    ['fluff/fluff', 'simonvh'],
    ['genipe/genipe', 'pgxcentre'],
    ['goldilocks/goldilocks', 'SamStudio8'],
    ['LipidFinder/LipidFinder', 'ODonnell-Lipidomics'],
    ['macsyfinder/macsypy', 'gem-pasteur'],
    ['msproteomicstools/msproteomicstoolslib', 'msproteomicstools'],
    ['neat-genreads', 'zstephens'],
    ['paleomix/paleomix', 'MikkelSchubert'],
    ['psamm/psamm', 'zhanglab'],
    ['pymbar/pymbar', 'choderalab'],
    ['pypdb/pypdb', 'williamgilpin'],
    ['pyvolve/src', 'sjspielman'],
    ['rnftools/rnftools', 'karel-brinda'],
    ['Scoary/scoary', 'AdmiralenOla'],
    ['spladder/spladder', 'ratschlab'],
    ['st_pipeline/stpipeline', 'SpatialTranscriptomicsResearch'],
    ['transit/src', 'mad-lab'],
    ['UMI-tools/umi_tools', 'CGATOxford'],
    ['umis/umis', 'vals'],
    ['ursgal/ursgal', 'ursgal']
]

for directory, author in tqdm(tuple(repo_directory_dict)):
    os.environ['PACKAGE_DIRECTORY'] = os.path.join('./github_repos', directory)
    package_name = directory.split('/')[-1]
    os.environ['PACKAGE_NAME'] = package_name
    os.environ['REPO_AUTHOR'] = author
    subprocess.run('python3 parse.py', shell=True)