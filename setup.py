from setuptools import setup, find_packages

setup(name='BioPharma',
      version='0.2',
      description='Modelling and optimisation of biopharmaceutical processes',
      url='https://github.com/UCL-Biochemical-Engineering/PyBioPharma',
      author='Jonathan Cooper',
      author_email='j.p.cooper@ucl.ac.uk',
      classifiers=['Development Status :: 3 - Alpha',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 3',
                   'Operating System :: OS Independent',
                   'Intended Audience :: Science/Research',
                   'License :: Other/Proprietary License'],
      install_requires=['pint>=0.8', 'Pyyaml', 'pandas', 'deap>=1.1.0'],
      python_requires='>=3.3',
      packages=find_packages(exclude=['*test']),
      package_data={
          'biopharma': ['../data/*', 'units.txt', '*.html']
      },
      zip_safe=False
      )
