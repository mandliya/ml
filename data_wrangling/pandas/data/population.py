#!/usr/bin/env python

import numpy as np
import pandas as pd
import os

data_file = os.path.join(os.path.dirname(__file__),'Top5000population.csv')

data = pd.read_csv(data_file, header=None, thousands=',',sep=',',
        names=['city','state','pop'],
        encoding='iso-8859-1')

data['city'] = data['city'].str.strip()
cities = [{'city':line[0],'state':line[1], 'pop':line[2]} for line in data.values]
