#!/usr/bin/env jython

'''
Rapid annotation service for brat using the National Library of Medicine (NLM)
MetaMap tool.

Author:     Pontus Stenetorp    <pontus stenetorp se>
Version:    2012-09-19
'''

from __future__ import with_statement

from java.lang import Class as JavaClass, ClassNotFoundException

from collections import defaultdict
from os.path import dirname, join as path_join
from sys import stderr

from config import (METAMAP_API_DIR, METAMAP_HOSTNAME, METAMAP_PORT,
        USE_SEM_GRP)
from jar import import_jar

### Constants
METAMAP_JAR_PATH = path_join(METAMAP_API_DIR, 'MetaMapApi.jar')
PROLOG_JAR_PATH = path_join(METAMAP_API_DIR, 'prologbeans.jar')
# The way they handle options is ugly beyond words, but let's do it live!
METAMAP_OPTIONS = (
        # Word Sense Disambiguation (WSD)
        '-y',
        )
RES_DIR = path_join(dirname(__file__), 'res')
SEM_TYPE_MAP_PATH = path_join(RES_DIR, 'SemanticTypeMappings_2011AA.txt')
SEM_GRPS_MAP_PATH = path_join(RES_DIR, 'SemGroups_2011.txt')
###

# We do dynamic loading to make the command-line less cumbersome
import_jar(METAMAP_JAR_PATH)
import_jar(PROLOG_JAR_PATH)

try:
    MetaMapApiImpl = JavaClass.forName(
            'gov.nih.nlm.nls.metamap.MetaMapApiImpl')
except ClassNotFoundException:
    print >> stderr, ('ERROR: Unable to instantiate MetaMapApi, is the '
            "following path '%s' really pointing to a directory "
            'containing the two MetaMap Java API JAR;s?') % METAMAP_API_DIR
    raise

def _get_sem_type_name_by_abbrv():
    sem_type_name_by_abbrv = {}
    with open(SEM_TYPE_MAP_PATH, 'r') as sem_type_map_file:
        for line in (l.rstrip('\n') for l in sem_type_map_file):
            abbrv, name = line.split('|')
            sem_type_name_by_abbrv[abbrv] = name
    return sem_type_name_by_abbrv

def _get_sem_grp_name_by_sem_type_name():
    sem_grp_name_by_sem_type_name = {}
    with open(SEM_GRPS_MAP_PATH, 'r') as sem_grps_map_file:
        for line in (l.rstrip('\n') for l in sem_grps_map_file):
            _, grp_name, _, type_name = line.split('|')
            sem_grp_name_by_sem_type_name[type_name] = grp_name
    return sem_grp_name_by_sem_type_name

def get_type_suggestions(token):
    ### Connect and set options
    api = MetaMapApiImpl(METAMAP_HOSTNAME, METAMAP_PORT)
    api.setOptions(METAMAP_OPTIONS)

    ### Get the results and do a standard Java interface dance
    results = api.processCitationsFromString(token)
    utterances = results.get(0).getUtteranceList()
    pcms = utterances.get(0).getPCMList()

    ### Collect the semantic type candidates and their scores
    # Load MetaMap mappings for semantic types
    sem_type_name_by_abbrv = _get_sem_type_name_by_abbrv()
    if USE_SEM_GRP:
        sem_grp_name_by_sem_type_name = _get_sem_grp_name_by_sem_type_name()

    score_by_candidate = defaultdict(lambda : float(2 ** 32))
    for candidate in pcms.get(0).getCandidateList():
        for sem_type_abbrv in candidate.getSemanticTypes():
            # Pick and potentially expand an non-abbreviated name
            sem_type_name = sem_type_name_by_abbrv[sem_type_abbrv]
            if USE_SEM_GRP:
                sem_type_name = sem_grp_name_by_sem_type_name[sem_type_name]

            # I think a low score is better
            score_by_candidate[sem_type_name] = min(candidate.score,
                    score_by_candidate[sem_type_name])

    ### Infer a somewhat probabalistic score for each type
    # Note: Danger! We now assume that scores are never positive!
    score_sum = float(abs(sum(score_by_candidate.itervalues())))
    res_pairs = []
    for candidate, score in score_by_candidate.iteritems():
        probability = abs(score) / score_sum
        res_pairs.append((probability, candidate))
    res_pairs.sort(reverse=True)
    return res_pairs

def main(args):
    # Some test code
    from sys import stdin
    for line in (l.rstrip('\n') for l in stdin):
        print '%s\t%s' % (line, get_type_suggestions(line))

    return 0

if __name__ == '__main__':
    from sys import argv
    exit(main(argv))
