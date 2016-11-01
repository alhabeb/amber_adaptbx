#! /usr/bin/env phenix.python

# Romain M. Wolf, NIBR Basel, December 2013
# with revisions by Pawel Janowski & Jason Swails, Rutgers U., Feb. 2014
#    & Jan. 2015

#  Copyright (c) 2013, Novartis Institutes for BioMedical Research Inc.
#  All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#     * Neither the name of Novartis Institutes for BioMedical Research Inc.
#       nor the names of its contributors may be used to endorse or promote
#       products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

__version__ = "1.2"
__date__ = "January 2015"

# PDB analyzer to prepare protein(-ligand) PDB files for Amber simulations.

import os
import sys
from cStringIO import StringIO
from optparse import OptionParser
from math import sqrt
import subprocess

from libtbx.utils import Sorry
import signal


def sigint_handler(*args, **kwargs):
  print >> sys.stderr, "Interrupt signal caught. Exiting"
  sys.exit(1)

signal.signal(signal.SIGINT, sigint_handler)

# Global constants
RESPROT = ('ALA', 'ARG', 'ASN', 'ASP',
           'CYS', 'GLN', 'GLU', 'GLY',
           'HIS', 'ILE', 'LEU', 'LYS',
           'MET', 'PHE', 'PRO', 'SER',
           'THR', 'TRP', 'TYR', 'VAL',
           'HID', 'HIE', 'HIN', 'HIP',
           'CYX', 'ASH', 'GLH', 'LYH',
           'ACE', 'NME', 'GL4', 'AS4')

RESNA = ('  C', '  G', '  U', '  A',
         ' DC', ' DG', ' DT', ' DA')

RESSOLV = ('WAT', 'HOH',
           'AG', 'AL', 'Ag', 'BA', 'BR', 'Be', 'CA', 'CD',
           'CE', 'CL', 'CO', 'CR', 'CS', 'CU', 'CU1', 'Ce',
           'Cl-', 'Cr', 'Dy',
           'EU', 'EU3', 'Er', 'F', 'FE', 'FE2', 'GD3', 'HE+',
           'HG', 'HZ+', 'Hf', 'IN', 'IOD', 'K', 'K+', 'LA',
           'LI', 'LU', 'MG', 'MN', 'NA', 'NH4', 'NI', 'Na+',
           'Nd', 'PB', 'PD', 'PR', 'PT', 'Pu', 'RB', 'Ra',
           'SM', 'SR', 'Sm', 'Sn', 'TB', 'TL', 'Th', 'Tl',
           'Tm', 'U4+', 'V2+', 'Y', 'YB2', 'ZN', 'Zr')

#  Following not used right now; probably needs an flag to indicate that
#    we expect sugar residues in the input pdb file.)

RESSUGAR = ('0AA', '0AB', '0AD', '0AU', '0BA', '0BB', '0BC', '0BD', '0BU', '0CA',
            '0CB', '0CD', '0CU', '0DA', '0DB', '0DD', '0DU', '0EA', '0EB', '0FA',
            '0FB', '0GA', '0GB', '0GL', '0HA', '0HB', '0JA', '0JB', '0JD', '0JU',
            '0KA', '0KB', '0LA', '0LB', '0MA', '0MB', '0NA', '0NB', '0OA', '0OB',
            '0PA', '0PB', '0PD', '0PU', '0QA', '0QB', '0RA', '0RB', '0RD', '0RU',
            '0SA', '0SB', '0TA', '0TB', '0TV', '0Tv', '0UA', '0UB', '0VA', '0VB',
            '0WA', '0WB', '0XA', '0XB', '0XD', '0XU', '0YA', '0YB', '0ZA', '0ZB',
            '0aA', '0aB', '0aD', '0aU', '0bA', '0bB', '0bC', '0bD', '0bU', '0cA',
            '0cB', '0cD', '0cU', '0dA', '0dB', '0dD', '0dU', '0eA', '0eB', '0fA',
            '0fB', '0gA', '0gB', '0gL', '0hA', '0hB', '0jA', '0jB', '0jD', '0jU',
            '0kA', '0kB', '0lA', '0lB', '0mA', '0mB', '0nA', '0nB', '0oA', '0oB',
            '0pA', '0pB', '0pD', '0pU', '0qA', '0qB', '0rA', '0rB', '0rD', '0rU',
            '0sA', '0sB', '0tA', '0tB', '0tV', '0tv', '0uA', '0uB', '0vA', '0vB',
            '0wA', '0wB', '0xA', '0xB', '0xD', '0xU', '0yA', '0yB', '0zA', '0zB',
            '1AA', '1AB', '1AD', '1AU', '1BA', '1BB', '1BD', '1BU', '1CA', '1CB',
            '1CD', '1CU', '1DA', '1DB', '1DD', '1DU', '1EA', '1EB', '1FA', '1FB',
            '1GA', '1GB', '1HA', '1HB', '1JA', '1JB', '1JD', '1JU', '1KA', '1KB',
            '1LA', '1LB', '1MA', '1MB', '1NA', '1NB', '1OA', '1OB', '1PA', '1PB',
            '1PD', '1PU', '1QA', '1QB', '1RA', '1RB', '1RD', '1RU', '1TA', '1TB',
            '1TV', '1Tv', '1UA', '1UB', '1VA', '1VB', '1WA', '1WB', '1XA', '1XB',
            '1XD', '1XU', '1YA', '1YB', '1ZA', '1ZB', '1aA', '1aB', '1aD', '1aU',
            '1bA', '1bB', '1bD', '1bU', '1cA', '1cB', '1cD', '1cU', '1dA', '1dB',
            '1dD', '1dU', '1eA', '1eB', '1fA', '1fB', '1gA', '1gB', '1hA', '1hB',
            '1jA', '1jB', '1jD', '1jU', '1kA', '1kB', '1lA', '1lB', '1mA', '1mB',
            '1nA', '1nB', '1oA', '1oB', '1pA', '1pB', '1pD', '1pU', '1qA', '1qB',
            '1rA', '1rB', '1rD', '1rU', '1tA', '1tB', '1tV', '1tv', '1uA', '1uB',
            '1vA', '1vB', '1wA', '1wB', '1xA', '1xB', '1xD', '1xU', '1yA', '1yB',
            '1zA', '1zB', '2AA', '2AB', '2AD', '2AU', '2BA', '2BB', '2BD', '2BU',
            '2CA', '2CB', '2CD', '2CU', '2DA', '2DB', '2DD', '2DU', '2EA', '2EB',
            '2FA', '2FB', '2GA', '2GB', '2HA', '2HB', '2JA', '2JB', '2JD', '2JU',
            '2KA', '2KB', '2LA', '2LB', '2MA', '2MB', '2NA', '2NB', '2OA', '2OB',
            '2PA', '2PB', '2PD', '2PU', '2QA', '2QB', '2RA', '2RB', '2RD', '2RU',
            '2TA', '2TB', '2TV', '2Tv', '2UA', '2UB', '2XA', '2XB', '2XD', '2XU',
            '2ZA', '2ZB', '2aA', '2aB', '2aD', '2aU', '2bA', '2bB', '2bD', '2bU',
            '2cA', '2cB', '2cD', '2cU', '2dA', '2dB', '2dD', '2dU', '2eA', '2eB',
            '2fA', '2fB', '2gA', '2gB', '2hA', '2hB', '2jA', '2jB', '2jD', '2jU',
            '2kA', '2kB', '2lA', '2lB', '2mA', '2mB', '2nA', '2nB', '2oA', '2oB',
            '2pA', '2pB', '2pD', '2pU', '2qA', '2qB', '2rA', '2rB', '2rD', '2rU',
            '2tA', '2tB', '2tV', '2tv', '2uA', '2uB', '2xA', '2xB', '2xD', '2xU',
            '2zA', '2zB', '3AA', '3AB', '3AD', '3AU', '3BA', '3BB', '3BC', '3BD',
            '3BU', '3CA', '3CB', '3CD', '3CU', '3DA', '3DB', '3DD', '3DU', '3EA',
            '3EB', '3FA', '3FB', '3GA', '3GB', '3HA', '3HB', '3JA', '3JB', '3JD',
            '3JU', '3KA', '3KB', '3LA', '3LB', '3MA', '3MB', '3NA', '3NB', '3OA',
            '3OB', '3PA', '3PB', '3PD', '3PU', '3QA', '3QB', '3RA', '3RB', '3RD',
            '3RU', '3TA', '3TB', '3UA', '3UB', '3VA', '3VB', '3WA', '3WB', '3XA',
            '3XB', '3XD', '3XU', '3YA', '3YB', '3ZA', '3ZB', '3aA', '3aB', '3aD',
            '3aU', '3bA', '3bB', '3bC', '3bD', '3bU', '3cA', '3cB', '3cD', '3cU',
            '3dA', '3dB', '3dD', '3dU', '3eA', '3eB', '3fA', '3fB', '3gA', '3gB',
            '3hA', '3hB', '3jA', '3jB', '3jD', '3jU', '3kA', '3kB', '3lA', '3lB',
            '3mA', '3mB', '3nA', '3nB', '3oA', '3oB', '3pA', '3pB', '3pD', '3pU',
            '3qA', '3qB', '3rA', '3rB', '3rD', '3rU', '3tA', '3tB', '3uA', '3uB',
            '3vA', '3vB', '3wA', '3wB', '3xA', '3xB', '3xD', '3xU', '3yA', '3yB',
            '3zA', '3zB', '4AA', '4AB', '4BA', '4BB', '4BD', '4BU', '4CA', '4CB',
            '4CD', '4CU', '4DA', '4DB', '4EA', '4EB', '4FA', '4FB', '4GA', '4GB',
            '4GL', '4HA', '4HB', '4JA', '4JB', '4JD', '4JU', '4KA', '4KB', '4LA',
            '4LB', '4MA', '4MB', '4NA', '4NB', '4OA', '4OB', '4PA', '4PB', '4PD',
            '4PU', '4QA', '4QB', '4RA', '4RB', '4SA', '4SB', '4TA', '4TB', '4TV',
            '4Tv', '4UA', '4UB', '4VA', '4VB', '4WA', '4WB', '4XA', '4XB', '4YA',
            '4YB', '4ZA', '4ZB', '4aA', '4aB', '4bA', '4bB', '4bD', '4bU', '4cA',
            '4cB', '4cD', '4cU', '4dA', '4dB', '4eA', '4eB', '4fA', '4fB', '4gA',
            '4gB', '4gL', '4hA', '4hB', '4jA', '4jB', '4jD', '4jU', '4kA', '4kB',
            '4lA', '4lB', '4mA', '4mB', '4nA', '4nB', '4oA', '4oB', '4pA', '4pB',
            '4pD', '4pU', '4qA', '4qB', '4rA', '4rB', '4sA', '4sB', '4tA', '4tB',
            '4tV', '4tv', '4uA', '4uB', '4vA', '4vB', '4wA', '4wB', '4xA', '4xB',
            '4yA', '4yB', '4zA', '4zB', '5AD', '5AU', '5BA', '5BB', '5CA', '5CB',
            '5DD', '5DU', '5JA', '5JB', '5PA', '5PB', '5RD', '5RU', '5XD', '5XU',
            '5aD', '5aU', '5bA', '5bB', '5cA', '5cB', '5dD', '5dU', '5jA', '5jB',
            '5pA', '5pB', '5rD', '5rU', '5xD', '5xU', '6BD', '6BU', '6CD', '6CU',
            '6EA', '6EB', '6GA', '6GB', '6JD', '6JU', '6KA', '6KB', '6LA', '6LB',
            '6MA', '6MB', '6NA', '6NB', '6PD', '6PU', '6TA', '6TB', '6VA', '6VB',
            '6WA', '6WB', '6YA', '6YB', '6bD', '6bU', '6cD', '6cU', '6eA', '6eB',
            '6gA', '6gB', '6jD', '6jU', '6kA', '6kB', '6lA', '6lB', '6mA', '6mB',
            '6nA', '6nB', '6pD', '6pU', '6tA', '6tB', '6vA', '6vB', '6wA', '6wB',
            '6yA', '6yB', '7GL', '7SA', '7SB', '7gL', '7sA', '7sB', '8GL', '8SA',
            '8SB', '8gL', '8sA', '8sB', '9GL', '9SA', '9SB', '9gL', '9sA', '9sB',
            'ACX', 'AGL', 'ASA', 'ASB', 'AgL', 'AsA', 'AsB', 'BGL', 'BSA', 'BSB',
            'BgL', 'BsA', 'BsB', 'CA2', 'CGL', 'CSA', 'CSB', 'CgL', 'CsA', 'CsB',
            'DGL', 'DSA', 'DSB', 'DgL', 'DsA', 'DsB', 'EGL', 'ESA', 'ESB', 'EgL',
            'EsA', 'EsB', 'FGL', 'FSA', 'FSB', 'FgL', 'FsA', 'FsB', 'GGL', 'GSA',
            'GSB', 'GgL', 'GsA', 'GsB', 'HGL', 'HSA', 'HSB', 'HgL', 'HsA', 'HsB',
            'IGL', 'ISA', 'ISB', 'IgL', 'IsA', 'IsB', 'JGL', 'JSA', 'JSB', 'JgL',
            'JsA', 'JsB', 'KGL', 'KSA', 'KSB', 'KgL', 'KsA', 'KsB', 'MEX', 'NLN',
            'OLS', 'OLT', 'OME', 'PEA', 'PEB', 'PGA', 'PGB', 'PKA', 'PKB', 'PLA',
            'PLB', 'PMA', 'PMB', 'PNA', 'PNB', 'PTA', 'PTB', 'PeA', 'PeB', 'PgA',
            'PgB', 'PkA', 'PkB', 'PlA', 'PlB', 'PmA', 'PmB', 'PnA', 'PnB', 'PtA',
            'PtB', 'QBD', 'QBU', 'QCD', 'QCU', 'QEA', 'QEB', 'QGA', 'QGB', 'QJD',
            'QJU', 'QKA', 'QKB', 'QLA', 'QLB', 'QMA', 'QMB', 'QNA', 'QNB', 'QPD',
            'QPU', 'QTA', 'QTB', 'QVA', 'QVB', 'QWA', 'QWB', 'QYA', 'QYB', 'QbD',
            'QbU', 'QcD', 'QcU', 'QeA', 'QeB', 'QgA', 'QgB', 'QjD', 'QjU', 'QkA',
            'QkB', 'QlA', 'QlB', 'QmA', 'QmB', 'QnA', 'QnB', 'QpD', 'QpU', 'QtA',
            'QtB', 'QvA', 'QvB', 'QwA', 'QwB', 'QyA', 'QyB', 'REA', 'REB', 'RGA',
            'RGB', 'RKA', 'RKB', 'RLA', 'RLB', 'RMA', 'RMB', 'RNA', 'RNB', 'ROH',
            'RTA', 'RTB', 'ReA', 'ReB', 'RgA', 'RgB', 'RkA', 'RkB', 'RlA', 'RlB',
            'RmA', 'RmB', 'RnA', 'RnB', 'RtA', 'RtB', 'SEA', 'SEB', 'SGA', 'SGB',
            'SKA', 'SKB', 'SLA', 'SLB', 'SMA', 'SMB', 'SNA', 'SNB', 'STA', 'STB',
            'SO3', 'SeA', 'SeB', 'SgA', 'SgB', 'SkA', 'SkB', 'SlA', 'SlB', 'SmA',
            'SmB', 'SnA', 'SnB', 'StA', 'StB', 'TAA', 'TAB', 'TBT', 'TDA', 'TDB',
            'TEA', 'TEB', 'TFA', 'TFB', 'TGA', 'TGB', 'THA', 'THB', 'TKA', 'TKB',
            'TLA', 'TLB', 'TMA', 'TMB', 'TNA', 'TNB', 'TOA', 'TOB', 'TQA', 'TQB',
            'TRA', 'TRB', 'TTA', 'TTB', 'TUA', 'TUB', 'TXA', 'TXB', 'TZA', 'TZB',
            'TaA', 'TaB', 'TdA', 'TdB', 'TeA', 'TeB', 'TfA', 'TfB', 'TgA', 'TgB',
            'ThA', 'ThB', 'TkA', 'TkB', 'TlA', 'TlB', 'TmA', 'TmB', 'TnA', 'TnB',
            'ToA', 'ToB', 'TqA', 'TqB', 'TrA', 'TrB', 'TtA', 'TtB', 'TuA', 'TuB',
            'TxA', 'TxB', 'TzA', 'TzB', 'UBD', 'UBU', 'UCD', 'UCU', 'UEA', 'UEB',
            'UGA', 'UGB', 'UJD', 'UJU', 'UKA', 'UKB', 'ULA', 'ULB', 'UMA', 'UMB',
            'UNA', 'UNB', 'UPD', 'UPU', 'UTA', 'UTB', 'UVA', 'UVB', 'UWA', 'UWB',
            'UYA', 'UYB', 'UbD', 'UbU', 'UcD', 'UcU', 'UeA', 'UeB', 'UgA', 'UgB',
            'UjD', 'UjU', 'UkA', 'UkB', 'UlA', 'UlB', 'UmA', 'UmB', 'UnA', 'UnB',
            'UpD', 'UpU', 'UtA', 'UtB', 'UvA', 'UvB', 'UwA', 'UwB', 'UyA', 'UyB',
            'VBD', 'VBU', 'VCD', 'VCU', 'VEA', 'VEB', 'VGA', 'VGB', 'VJD', 'VJU',
            'VKA', 'VKB', 'VLA', 'VLB', 'VMA', 'VMB', 'VNA', 'VNB', 'VPD', 'VPU',
            'VTA', 'VTB', 'VVA', 'VVB', 'VWA', 'VWB', 'VYA', 'VYB', 'VbD', 'VbU',
            'VcD', 'VcU', 'VeA', 'VeB', 'VgA', 'VgB', 'VjD', 'VjU', 'VkA', 'VkB',
            'VlA', 'VlB', 'VmA', 'VmB', 'VnA', 'VnB', 'VpD', 'VpU', 'VtA', 'VtB',
            'VvA', 'VvB', 'VwA', 'VwB', 'VyA', 'VyB', 'WAA', 'WAB', 'WBA', 'WBB',
            'WBD', 'WBU', 'WCA', 'WCB', 'WCD', 'WCU', 'WDA', 'WDB', 'WEA', 'WEB',
            'WFA', 'WFB', 'WGA', 'WGB', 'WHA', 'WHB', 'WJA', 'WJB', 'WJD', 'WJU',
            'WKA', 'WKB', 'WLA', 'WLB', 'WMA', 'WMB', 'WNA', 'WNB', 'WOA', 'WOB',
            'WPA', 'WPB', 'WPD', 'WPU', 'WQA', 'WQB', 'WRA', 'WRB', 'WTA', 'WTB',
            'WUA', 'WUB', 'WVA', 'WVB', 'WWA', 'WWB', 'WXA', 'WXB', 'WYA', 'WYB',
            'WZA', 'WZB', 'WaA', 'WaB', 'WbA', 'WbB', 'WbD', 'WbU', 'WcA', 'WcB',
            'WcD', 'WcU', 'WdA', 'WdB', 'WeA', 'WeB', 'WfA', 'WfB', 'WgA', 'WgB',
            'WhA', 'WhB', 'WjA', 'WjB', 'WjD', 'WjU', 'WkA', 'WkB', 'WlA', 'WlB',
            'WmA', 'WmB', 'WnA', 'WnB', 'WoA', 'WoB', 'WpA', 'WpB', 'WpD', 'WpU',
            'WqA', 'WqB', 'WrA', 'WrB', 'WtA', 'WtB', 'WuA', 'WuB', 'WvA', 'WvB',
            'WwA', 'WwB', 'WxA', 'WxB', 'WyA', 'WyB', 'WzA', 'WzB', 'XEA', 'XEB',
            'XGA', 'XGB', 'XKA', 'XKB', 'XLA', 'XLB', 'XMA', 'XMB', 'XNA', 'XNB',
            'XTA', 'XTB', 'XeA', 'XeB', 'XgA', 'XgB', 'XkA', 'XkB', 'XlA', 'XlB',
            'XmA', 'XmB', 'XnA', 'XnB', 'XtA', 'XtB', 'YAA', 'YAB', 'YDA', 'YDB',
            'YEA', 'YEB', 'YFA', 'YFB', 'YGA', 'YGB', 'YHA', 'YHB', 'YKA', 'YKB',
            'YLA', 'YLB', 'YMA', 'YMB', 'YNA', 'YNB', 'YOA', 'YOB', 'YQA', 'YQB',
            'YRA', 'YRB', 'YTA', 'YTB', 'YTV', 'YTv', 'YUA', 'YUB', 'YXA', 'YXB',
            'YZA', 'YZB', 'YaA', 'YaB', 'YdA', 'YdB', 'YeA', 'YeB', 'YfA', 'YfB',
            'YgA', 'YgB', 'YhA', 'YhB', 'YkA', 'YkB', 'YlA', 'YlB', 'YmA', 'YmB',
            'YnA', 'YnB', 'YoA', 'YoB', 'YqA', 'YqB', 'YrA', 'YrB', 'YtA', 'YtB',
            'YtV', 'Ytv', 'YuA', 'YuB', 'YxA', 'YxB', 'YzA', 'YzB', 'ZAA', 'ZAB',
            'ZAD', 'ZAU', 'ZDA', 'ZDB', 'ZDD', 'ZDU', 'ZEA', 'ZEB', 'ZFA', 'ZFB',
            'ZGA', 'ZGB', 'ZHA', 'ZHB', 'ZKA', 'ZKB', 'ZLA', 'ZLB', 'ZMA', 'ZMB',
            'ZNA', 'ZNB', 'ZOA', 'ZOB', 'ZOLS', 'ZOLT', 'ZQA', 'ZQB', 'ZRA', 'ZRB',
            'ZRD', 'ZRU', 'ZTA', 'ZTB', 'ZUA', 'ZUB', 'ZXA', 'ZXB', 'ZXD', 'ZXU',
            'ZZA', 'ZZB', 'ZaA', 'ZaB', 'ZaD', 'ZaU', 'ZdA', 'ZdB', 'ZdD', 'ZdU',
            'ZeA', 'ZeB', 'ZfA', 'ZfB', 'ZgA', 'ZgB', 'ZhA', 'ZhB', 'ZkA', 'ZkB',
            'ZlA', 'ZlB', 'ZmA', 'ZmB', 'ZnA', 'ZnB', 'ZoA', 'ZoB', 'ZqA', 'ZqB',
            'ZrA', 'ZrB', 'ZrD', 'ZrU', 'ZtA', 'ZtB', 'ZuA', 'ZuB', 'ZxA', 'ZxB',
            'ZxD', 'ZxU', 'ZzA', 'ZzB', '0AE', '2AE', '4AE', 'YGa', '0AF', '2AF',
            '4AF', 'YAF', '0dR', '3dR', '4dR', 'WdR')


#=============================================
def pdb_read(pdbin, noter, model):
  #=============================================
  # only records starting with the following strings are kept...
  if noter:
    ACCEPTED = ('ATOM', 'HETATM')
  else:
    ACCEPTED = ('ATOM', 'HETATM', 'TER', 'MODEL', 'ENDMDL')
# records starting with the following strings are considered 'dividers'
# and they are cleaned for the rest of the line...
  DIVIDERS = ('TER', 'MODEL', 'ENDMDL')

  if pdbin == 'stdin':
    records = sys.stdin
  elif hasattr(pdbin, 'readline'):
    records = pdbin
  else:
    records = open(pdbin, 'r')
  print >> sys.stderr, "\n=================================================="
  print >> sys.stderr, "Summary of pdb4amber for file %s" % pdbin
  print >> sys.stderr, "=================================================="
  '''
  This PDB reader first splits PDB lines (records) into individual (named) fields,
  then later re-assembles the fields in records. This might be done more elegantly,
  but we keep this scheme for now for clarity (given the messy PDB file format)!

    record_type     0    atom_number     1    blank1           2
    atom_name       3    alt_loc_ind     4    residue_name     5
    blank2          6    chain_id        7    residue_number   8
    insertion_code  9    blank3         10    x               11
    y               12   z              13    occupancy       14
    bfactor         15   blank4         16    element         17
    charge          18

  '''

  record_type = []
  atom_number = []
  blank1 = []
  atom_name = []
  alt_loc_ind = []
  residue_name = []
  blank2 = []
  chain_id = []
  residue_number = []
  insertion_code = []
  blank3 = []
  x = []
  y = []
  z = []
  occupancy = []
  bfactor = []
  blank4 = []
  element = []
  charge = []
# keep everything in 'ACCEPTED'
  lines = records.readlines()

  if model != 0:
    import re
    start, end = -1, -1
    for i, line in enumerate(lines):
      if re.search(r'^MODEL\s+%d\s' % model, line):
        start = i
        break
    for i in range(start, len(lines)):
      if lines[i][0:6] == 'ENDMDL':
        end = i
        break
    assert start != -1, "Requested MODEL %d not found." % model
    assert end != -1, "ENDMDL line after MODEL %d not found." % model
    lines = lines[start:end]
    # import code; code.interact(local=dict(globals(), **locals()))

  for line in lines:
    # make all lines 80 characters long (fill up with blanks if necessary)
    # so that the line parser will not fail on shorter lines...
    line = (line.rstrip() + (80 - len(line)) * ' ')
    if line[0:6].rstrip() not in ACCEPTED:
      #~ print >> sys.stderr, '%-6sk' %line[0:6].rstrip()
      continue
# make clean divider lines without additional stuff that might hurt later
    elif line[0:6].rstrip() in DIVIDERS:
      if line[0:5] == 'MODEL':
        line = line.rstrip()
      else:
        line = line[0:6].rstrip()
      line = (line + (80 - len(line)) * ' ')
    else:
      pass
# split the line into records
    record_type.append('%-6s' % line[0:6])
    atom_number.append(line[6:11])
    blank1.append(line[11:12])
    atom_name.append(line[12:16])
    alt_loc_ind.append(line[16:17])
    residue_name.append(line[17:20])
    blank2.append(line[20:21])
    chain_id.append(line[21:22])
    residue_number.append(line[22:26])
    insertion_code.append(line[26:27])
    blank3.append(line[27:30])
    x.append(line[30:38])
    y.append(line[38:46])
    z.append(line[46:54])
    occupancy.append(line[54:60])
    bfactor.append(line[60:66])
    blank4.append(line[66:76])
    element.append(line[76:78])
    charge.append(line[78:80])
  insert_resnums = []
  insert_resnames = []
  chains = []
  recordlist = []
  for i, record in enumerate(record_type):
    # determine insertion code
    if insertion_code[i] != ' ' and residue_number[i] + insertion_code[i] not in insert_resnums:
      insert_resnums.append(residue_number[i] + insertion_code[i])
      insert_resnames.append(residue_name[i])
# determine chain id and record it, if not yet found before
    if chain_id[i] != ' ' and chain_id[i] not in chains:
      chains.append(chain_id[i])
    record = [record_type[i], atom_number[i], blank1[i], atom_name[i], alt_loc_ind[i],
              residue_name[i], blank2[i], chain_id[i], residue_number[i],
              insertion_code[i], blank3[i], x[i], y[i], z[i],
              occupancy[i], bfactor[i], blank4[i], element[i], charge[i]]
# append the accepted record to the overlall record list
    recordlist.append(record)
# report findings so far to the screen
  if chains:
    print >> sys.stderr, "\n----------Chains"
    print >> sys.stderr, "The following (original) chains have been found:"
    for chain in chains:
      print >> sys.stderr, chain
  if insert_resnums:
    print >> sys.stderr, "\n----------Insertions"
    print >> sys.stderr, "The following (original-number) residues were considered as insertions:"
    print >> sys.stderr, "They will be renumbered 'normally' in the final 1-N sequence."
    for i in range(0, len(insert_resnums)):
      print >> sys.stderr, "%s%s" % (insert_resnames[i], (insert_resnums[i]))

  return recordlist

#==================================================


def pdb_write(recordlist, filename, cnct=''):
  #==================================================
  # uses a record list as created in pdb_read and writes it out to the filename
  # using the format below
  if filename == 'stdout':
    pdbout = sys.stdout
  else:
    pdbout = open(filename, 'w')
  format = "%6s%5s%1s%4s%1s%3s%1s%1s%4s%1s%3s%8s%8s%8s%6s%6s%10s%2s%2s\n"
  for i, record in enumerate(recordlist):
    # avoid overflow for atom and residue numbers:
    if isinstance(record[1], (int, long)):
      record[1] = record[1] % 100000
    if isinstance(record[8], (int, long)):
      record[8] = record[8] % 10000
    pdbout.write(format % tuple(record))
  pdbout.write(cnct)
  pdbout.write('END' + (77 * ' ') + '\n')
  if pdbout != sys.stdout:
    pdbout.close()

#==================================================


def prot_only(recordlist):
  #==================================================
  # this strips any residues not recognized by Amber libraries...
  # in a personalized Amber installation with additional libraries,
  # you might consider extending this list
  global RESPROT, RESNA
  protlist = []
  for record in recordlist:
    if record[5] not in RESPROT and record[5] not in RESNA:
      continue
    else:
      protlist.append(record)
  return protlist

#==================================================


def remove_hydrogens(recordlist):
  #==================================================
  nohlist = []

  for record in recordlist:
    if record[3][0] == 'H' or record[3][0:2] == ' H' \
            or record[3][0:2] == '1H' or record[3][0:2] == '2H' or record[3][0:2] == '3H' \
            or record[3][0:3] == ' 1H' or record[3][0:3] == ' 2H' or record[3][0:3] == ' 3H':
      continue
    else:
      nohlist.append(record)

# return the record list with all hydrogens removed
  return nohlist

#========================================


def remove_water(recordlist, filename):
  #========================================
  # removes all water molecules of option -d was specified
  drylist = []
  waterlist = []
  nwaters = 0
  is_prev_water = 0
# format = "%6s%5s%1s%4s%1s%3s%1s%1s%4s%1s%3s%8s%8s%8s%6s%6s%10s%2s%2s\n"
# watpdb = open(filename+'_water.pdb', 'w')
  for record in recordlist:
    # if previous record was water, remove TER card
    if is_prev_water and record[0] == 'TER   ':
      is_prev_water = 0
# if oxygen, then count water
    elif (record[5] == 'HOH' or record[5] == 'WAT') and 'O' in record[3]:
      nwaters += 1
      waterlist.append(record)
      is_prev_water = 1
#     watpdb.write(format % tuple(record))
      continue
# if not oxygen, just remove, but do not count, since this is probably hydrogen
    elif record[5] == 'HOH' or record[5] == 'WAT':
      is_prev_water = 1
      continue
    else:
      drylist.append(record)
      is_prev_water = 0

# report the water removal to the screen
  print >> sys.stderr, "\n---------- Water"
  print >> sys.stderr, "%d water molecules have been removed" % nwaters
  print >> sys.stderr, "and stored in the file %s_water.pdb" % filename
# return the dry record list with all water removed
  pdb_write(waterlist, filename + '_water.pdb')
  return drylist

#========================================


def remove_mostpop_altloc(recordlist, filename):
  #========================================
  noaltlist = []
  minor_altloc = open(filename + '_minor_altloc.pdb', 'w')
  pdbformat = "%6s%5s%1s%4s%1s%3s%1s%1s%4s%1s%3s%8s%8s%8s%6s%6s%10s%2s%2s\n"
  report_list = []

# keep most populous conformation
  import collections
  # n_altlocs is a dict where key is a unique atom identifier and value is
  # a two element list. First element contains list of occupancy values
  # of all occurrences of that atom. Second element counts the appearance
  # of the atom during the second iteration.
  n_altlocs = collections.OrderedDict()
# first iteration to set up dict with occupancies for each altloc atom
  for record in recordlist:
    id = "%s_%s" % (record[8], record[3])
    if record[4] != ' ':
      if id not in n_altlocs.keys():
        n_altlocs[id] = [[float(record[14])], 0]
      else:
        n_altlocs[id][0].append(float(record[14]))

# now iterate again.
  for record in recordlist:
    id = "%s_%s" % (record[8], record[3])
    if id in n_altlocs.keys():
      # find index of highest occupancy occurence
      alt_max = n_altlocs[id][0].index(max(n_altlocs[id][0]))
      # if current atom has highest occupancy altloc, add to list
      if n_altlocs[id][1] == alt_max:
        record[4] = ' '
        noaltlist.append(record)
        report_list.append(record)
      # otherwise write to minor_altloc file and discard
      else:
        minor_altloc.write(pdbformat % tuple(record))
      n_altlocs[id][1] += 1
    # if current atom has no altlocs, add directly to list
    else:
      record[4] = ' '
      noaltlist.append(record)

  if n_altlocs:
    print >> sys.stderr, "\n---------- Alternate Locations (Original Residues!)"
    print >> sys.stderr, "The following atoms had alternate locations:"
    for record in report_list:
      print >> sys.stderr, "%s_%-4s %s" % (record[5], record[8].strip(), record[3])
    print >> sys.stderr, "The alternate coordinates have been discarded."
    print >> sys.stderr, "Only the highest occupancy of each atom was kept."
    print >> sys.stderr, "Alternate conformations were printed to %s_minor_altloc.pdb" % filename

  minor_altloc.close()
  return noaltlist

#========================================


def remove_altloc(recordlist):
  #========================================
  noaltlist = []
  altloc_resnum = []
  altloc_resname = []
  for record in recordlist:
    # we accept only altlocs 'A' and '1'
    if record[4] != ' ' and record[4] != 'A' and record[4] != '1':
      if record[8] not in altloc_resnum:
        altloc_resnum.append(record[8])
        altloc_resname.append(record[5])
      continue

    else:
      record[4] = ' '
      noaltlist.append(record)
  if altloc_resnum:
    print >> sys.stderr, "\n---------- Alternate Locations (Original Residues!)"
    print >> sys.stderr, "The following residues had alternate locations:"

    for i, rname in enumerate(altloc_resname):
      print >> sys.stderr, "%s_%d" % (rname, int(altloc_resnum[i]))

    print >> sys.stderr, "The alternate coordinates have been discarded."
    print >> sys.stderr, "Only the first occurrence for each atom was kept."

  return noaltlist

#==================================================


def atom_wrap(recordlist):
  #==================================================
  # !!! this function should always be called !!!

  # wraps 4-letter hydrogens
  wraplist = []

  for record in recordlist:
    if record[0] != 'ATOM  ' and record[0] != 'HETATM':
      wraplist.append(record)
      continue

# shifts 3-letter atoms if needed
    elif record[3][0] != ' ' and record[3][3] == ' ':
      atomname = record[3][3] + record[3][0:3]
      record[3] = atomname
      wraplist.append(record)
      continue

    else:
      wraplist.append(record)
      continue

  return wraplist

#========================================


def renumber(recordlist, filename):
  #========================================
  table = open('%s_renum.txt' % filename, 'w')
  renumbered = []
  current = -100
  iatom = 1
  original = []
  oriresname = []
  final = []
  finresname = []

  for record in recordlist:
    if not 'ATOM' in record[0] and not 'HETATM' in record[0]:
      renumbered.append(record)

    elif current == -100:
      actualnum = record[8] + record[9]
      actualname = record[5]
      if record[3] == ' CA ' or record[3] == 'CH3':
        original.append(record[8] + record[9])
        oriresname.append(record[5])

      record[8] = 1
      record[9] = ' '
      current = 1
      record[1] = iatom
      iatom += 1

      if record[3] == ' CA ' or record[3] == ' CH3':
        final.append(record[8])
        finresname.append(record[5])

      renumbered.append(record)

    elif record[8] + record[9] == actualnum and record[5] == actualname:

      if record[3] == ' CA ' or record[3] == ' CH3':
        original.append(record[8] + record[9])
        oriresname.append(record[5])

      record[8] = current
      record[9] = ' '
      record[1] = iatom
      iatom += 1

      if record[3] == ' CA ' or record[3] == ' CH3':
        final.append(record[8])
        finresname.append(record[5])
      renumbered.append(record)

    elif record[8] + record[9] != actualnum or record[5] != actualname:
      actualnum = record[8] + record[9]
      actualname = record[5]
      if record[3] == ' CA ' or record[3] == ' CH3':
        original.append(record[8] + record[9])
        oriresname.append(record[5])

      current += 1
      record[8] = current
      record[9] = ' '
      record[1] = iatom
      iatom += 1

      if record[3] == ' CA ' or record[3] == ' CH3':
        final.append(record[8])
        finresname.append(record[5])
      renumbered.append(record)

  for i in range(0, len(original)):
    table.write("%3s %5s    %3s %5s\n" % (oriresname[i], (original[i]),
                                          finresname[i], final[i]))

  return renumbered

#========================================


def non_standard(recordlist, filename):
  #========================================
  # define the common AA and less common AA names that make up proteins
  # and that are recognized by Amber routines in ATOM (or HETATM) records

  global RESPROT, RESNA, RESSOLV

  hetero = open(filename + '_nonprot.pdb', 'w')
  pdbformat = "%6s%5s%1s%4s%1s%3s%1s%1s%4s%1s%3s%8s%8s%8s%6s%6s%10s%2s%2s\n"
  ns_resname = []

  for record in recordlist:
    if record[5] not in RESPROT and record[5] not in RESNA and record[5].strip() not in RESSOLV and record[5] != '   ':
      hetero.write(pdbformat % tuple(record))
      if record[5] not in ns_resname:
        ns_resname.append(record[5])

  if ns_resname:
    print >> sys.stderr, "\n---------- Non-Standard Residues"
    print >> sys.stderr, "The following non-standard residue names in the original PDB file"
    print >> sys.stderr, "are not recognized by Amber and have been written to the separate"
    print >> sys.stderr, "file %s_nonprot.pdb" % filename
    print >> sys.stderr, "\n".join(ns_resname)

  return ns_resname

#========================================


def non_standard_elbow(recordlist):
  #========================================
  # define the common AA and less common AA names that make up proteins
  # and that are recognized by Amber routines in ATOM (or HETATM) records
  RES_PROT = ('A', 'A3', 'A5', 'ACE',
              'ALA', 'AN', 'ARG', 'ASH',
              'ASN', 'ASP', 'BA', 'BR',
              'C', 'C3', 'C5', 'CA',
              'CD', 'CL', 'CN', 'CO',
              'CS', 'CU', 'CYM', 'CYS',
              'CYX', 'DA', 'DA3', 'DA5',
              'DAN', 'DC', 'DC3', 'DC4',
              'DC5', 'DCN', 'DG', 'DG3',
              'DG5', 'DGN', 'DT', 'DT3',
              'DT5', 'DTN', 'EU', 'F',
              'FE2', 'G', 'G3', 'G5',
              'GLH', 'GLN', 'GLU', 'GLY',
              'GN', 'HG', 'HID', 'HIE',
              'HIP', 'HIS', 'HOH', 'HYP',
              'ILE', 'IOD', 'K', 'LEU',
              'LI', 'LYN', 'LYS', 'MET',
              'MG', 'MN', 'NA', 'NHE',
              'NI', 'NME', 'OHE', 'PB',
              'PD', 'PHE', 'PL3', 'PRO',
              'PT', 'RB', 'SER', 'SPC',
              'SPF', 'SPG', 'SR', 'T4E',
              'THR', 'TP3', 'TP4', 'TP5',
              'TPF', 'TRP', 'TYR', 'U',
              'U3', 'U5', 'UN', 'V2+',
              'VAL', 'WAT', 'YB2', 'ZN',
              )

  RES = RES_PROT

  pdbformat = "%6s%5s%1s%4s%1s%3s%1s%1s%4s%1s%3s%8s%8s%8s%6s%6s%10s%2s%2s\n"
  ns_resname = []

  for record in recordlist:
    if record[5].strip() not in RES and record[5] != '   ':
      # if 1st instance of this residue, add atom and get chain/resid
      if record[5].strip() not in ns_resname:
        ns_resname.append(record[5].strip())
        try:
          f.close()
        except:
          pass
        f = open('4antechamber_%s.pdb' % (record[5].strip()), 'w')
        resid = record[8]
        chain = record[7]
        f.write(pdbformat % tuple(record))
      else:
        # if next atom in the 1st instance of the residue, add atom
        if record[8] == resid and record[7] == chain:
          f.write(pdbformat % tuple(record))
        else:
          # if next instance of the residue, close f and continue
          if not f.closed:
            f.close()

  return ns_resname

#========================================


def find_his(recordlist):
  #========================================

  amber_hist = {}
  standard_hist = {}
  res_to_change = {}
  for record in recordlist:
    if record[5] in ('HID', 'HIP', 'HIE') and record[3] == ' CA ':
      amber_hist[record[8]] = record[5]
    if record[5] == 'HIS':
      if record[8] not in standard_hist:
        standard_hist[record[8]] = [record[3].strip()]
      else:
        standard_hist[record[8]].append(record[3].strip())

  print >> sys.stderr, "\n---------- Histidines (Renumbered Residues!)"
  if len(amber_hist) == 0 and len(standard_hist) == 0:
    print >> sys.stderr, "No histidine residues found."
    return recordlist

  if len(amber_hist) > 0:
    print >> sys.stderr, "The following histidine residues are already named according to Amber convention."
    for rnum, rname in amber_hist.iteritems():
      print >> sys.stderr, '%s_%d' % (rname, rnum)

  if len(standard_hist) > 0:
    for rnum, atoms in standard_hist.items():
      if 'HD1' in atoms and 'HE2' in atoms:
        res_to_change[rnum] = 'HIP'
        del standard_hist[rnum]
      elif 'HD1' in atoms and 'HE2' not in atoms:
        res_to_change[rnum] = 'HID'
        del standard_hist[rnum]
      elif 'HD1' not in atoms and 'HE2' in atoms:
        res_to_change[rnum] = 'HIE'
        del standard_hist[rnum]

  if len(res_to_change) > 0:
    print >> sys.stderr, "The following HIS residues will be changed to Amber convention names:"
    for rnum, rname in res_to_change.items():
      print >> sys.stderr, "HIS %d --> %s." % (rnum, rname)
    for record in recordlist:
      if record[8] in res_to_change.keys():
        record[5] = res_to_change[record[8]]

  if len(standard_hist) > 0:
    print >> sys.stderr, "It was not possible to determine the protonation state of the following HIS"
    print >> sys.stderr, "residues based on presence of hydrogens. Amber will consider them as HIE"
    print >> sys.stderr, "(epsilon-HIS) by default. If other protonation state desired change to HID"
    print >> sys.stderr, "(delta-HIS) or HIP (protonated HIS) by hand."
    for rnum in standard_hist.keys():
      print >> sys.stderr, "HIS_%d" % rnum

  return recordlist


#========================================
def constph(recordlist):
  #========================================
  print >> sys.stderr, "\n---------- Constant pH Simulation"
  as4, gl4, hip = [], [], []
  for record in recordlist:
    if record[5] == 'ASP':
      record[5] = 'AS4'
      as4.append(record[8])
    elif record[5] == 'GLU':
      record[5] = 'GL4'
      gl4.append(record[8])
    elif record[5] == 'HIS':
      record[5] = 'HIP'
      hip.append(record[8])
    else:
      continue

  print >> sys.stderr, "ASP --> AS4: %d" % len(set(as4))
  print >> sys.stderr, "GLU --> GL4: %d" % len(set(gl4))
  print >> sys.stderr, "HIS --> HIP: %d" % len(set(hip))

  return recordlist

#========================================


def find_disulfide(recordlist, filename):
  #========================================
  cys_residues = []
  cys_sgx = []
  cys_sgy = []
  cys_sgz = []
  cyx_residues = []
  cys_sqn = []
  ncys = 0
  ncyx = 0
  sslist = []

  print >> sys.stderr, "\n---------- Cysteines in Disulfide Bonds (Renumbered Residues!)"
  for record in recordlist:

    if 'SG' in record[3] and ('CYS' in record[5] or 'CYX' in record[5]):
      cys_residues.append(record[8])
      cys_sgx.append(record[11])
      cys_sgy.append(record[12])
      cys_sgz.append(record[13])
      cys_sqn.append(record[1])
      ncys += 1

  cnct = ''
  if ncys > 0:

    sslink = open('%s_sslink' % filename, 'w')
    dist = [[0 for i in range(ncys)] for j in range(ncys)]
    for i in range(0, ncys - 1):
      for j in range(i + 1, ncys):
        dx = float(cys_sgx[i]) - float(cys_sgx[j])
        dx2 = dx * dx
        dy = float(cys_sgy[i]) - float(cys_sgy[j])
        dy2 = dy * dy
        dz = float(cys_sgz[i]) - float(cys_sgz[j])
        dz2 = dz * dz
        dist[i][j] = sqrt(dx2 + dy2 + dz2)
        if 3.0 > dist[i][j] > 0.1:
          cyx_residues.append(cys_residues[i])
          cyx_residues.append(cys_residues[j])
          print >> sys.stderr, ("CYS_%s - CYS_%s: S-S distance = %f Ang." % (cys_residues[i],
                                                                             cys_residues[j], dist[i][j]))
          sslink.write('%s %s\n' % (cys_residues[i], cys_residues[j]))
          ncyx += 1
          cnct += 'CONECT%5d%5d\n' % (cys_sqn[i], cys_sqn[j])
          ssrecord = (cys_residues[i], cys_residues[j])
          sslist.append(ssrecord)

# rename the CYS to CYX for disulfide-involved cysteines
    for record in recordlist:
      if record[8] in cyx_residues:
        record[5] = 'CYX'
      else:
        continue
  if ncyx:
    print >> sys.stderr, "The above CYS have been renamed to CYX in the new PDB file."
    print >> sys.stderr, "Disulfide bond CONECT cards have been added to the new PDB file."

  else:
    print >> sys.stderr, "No disulfide bonds have been detected."
  return recordlist, cnct, sslist

#========================================


def find_gaps(recordlist):
  #========================================
  global RESPROT
  ca_atoms = []
  c_atoms = []
  n_atoms = []
  gaplist = []

  def is_ter(index):
    resnum = recordlist[index][8]
    next = 1
    while True:
      if recordlist[index + next][0] in ['TER   ', 'MODEL ', 'ENDMDL']:
        return True
      elif recordlist[index + next][8] == resnum:
        next += 1
      else:
        return False

  #  N.B.: following only finds gaps in protein chains!
  for i, record in enumerate(recordlist):
    if (record[3].strip() == 'CA' or
            record[3].strip() == 'CH3') and record[5] in RESPROT:
      ca_atoms.append(i)
    if record[3].strip() == 'C' and record[5] in RESPROT:
      c_atoms.append(i)
    if record[3].strip() == 'N' and record[5] in RESPROT:
      n_atoms.append(i)

  nca = len(ca_atoms)
  ngaps = 0

  for i in range(nca - 1):
    if is_ter(ca_atoms[i]):
      continue
    # Following is orignal code, depending only on CA positions:
    #ca1 = recordlist[ca_atoms[i]]
    #ca2 = recordlist[ca_atoms[i+1]]

    # Changed here to look at the C-N peptide bond distance:
    ca1 = recordlist[c_atoms[i]]
    ca2 = recordlist[n_atoms[i + 1]]

    dx = float(ca1[11]) - float(ca2[11])
    dy = float(ca1[12]) - float(ca2[12])
    dz = float(ca1[13]) - float(ca2[13])
    gap = sqrt(dx * dx + dy * dy + dz * dz)

    # if gap > 5.0:  #original version, for CA connectivity
    if gap > 2.0:
      gaprecord = (gap, ca1[5], int(ca1[8]), ca2[5], int(ca2[8]))
      gaplist.append(gaprecord)
      ngaps += 1

  if ngaps > 0:
    print >> sys.stderr, "\n---------- Gaps (Renumbered Residues!)"
    cformat = "gap of %lf A between %s %d and %s %d"

    for i, gaprecord in enumerate(gaplist):
      print >> sys.stderr, (cformat % tuple(gaprecord))
    print >> sys.stderr, "Phenix will assume that these are 'real' gaps."

  return(gaplist)

#========================================


def find_incomplete(recordlist):
  #========================================
  # finds residues with missing heavy atoms in the following list of residues;
  # dictionary with number of heavy atoms:
  # PAJ TODO:complete this list with nucleic acids
  HEAVY = {'ALA': 5,  'ARG': 11, 'ASN': 8,  'ASP': 8,
           'CYS': 6,  'GLN': 9,  'GLU': 9,  'GLY': 4,
           'HIS': 10, 'ILE': 8,  'LEU': 8,  'LYS': 9,
           'MET': 8,  'PHE': 11, 'PRO': 7,  'SER': 6,
           'THR': 7,  'TRP': 14, 'TYR': 12, 'VAL': 7,
           'HID': 10, 'HIE': 10, 'HIN': 10, 'HIP': 10,
           'CYX': 6,  'ASH': 8,  'GLH': 9,  'LYH': 9}
  print >> sys.stderr, '\n---------- Missing Heavy Atoms (Renumbered Residues!)'
  resnum = []
  resname = []
  resheavy = []
  flag = 0
  nheavy = 1
  length = len(recordlist)
  for i, record in enumerate(recordlist):
    if i == length - 1:
      for j, res in enumerate(resnum):
        missing = HEAVY[resname[j]] - resheavy[j]
        if missing > 0:
          flag = 1
          print >> sys.stderr, "%s_%s misses %d heavy atom(s)" % (resname[j], res, missing)
      if flag == 0:
        print >> sys.stderr, "None"
      return()
    if not HEAVY.has_key(record[5]):
      continue
    if recordlist[i + 1][8] == record[8]:
      nheavy += 1
    else:
      resnum.append(record[8])
      resname.append(record[5])
      resheavy.append(nheavy)
      nheavy = 1
      continue
  return()


def check_pdb4amber_output(log):
  for line in log:
    if line.find('misses') > -1:
      print line
      #raise Sorry("model has missing atoms")


class writer(object):

  def __init__(self, log):
    self.log = log

  def write(self, data):
    self.log.append(data)


def run(arg_pdbout, arg_pdbin,
        arg_nohyd=False,
        arg_dry=False,
        arg_prot=False,
        arg_noter=False,
        arg_constph=False,
        arg_mostpop=False,
        log=None,
        arg_reduce=False,
        arg_model=0,
        arg_elbow=False
        ):
  stderr = sys.stderr
  if log is not None:
    sys.stderr = writer(log)
  filename, extension = os.path.splitext(arg_pdbout)
  pdbin = arg_pdbin

  # optionally run reduce on input file
  if arg_reduce:
    if arg_pdbin == 'stdin':
      pdbfile = sys.stdin
    else:
      pdbfile = open(arg_pdbin, 'r')
    try:
      reduce = os.path.join(os.getenv('AMBERHOME') or '', 'bin', 'reduce')
      if not os.path.exists(reduce):
        reduce = 'reduce'
      process = subprocess.Popen([reduce, '-BUILD', '-NUC', '-'], stdin=pdbfile,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      out, err = process.communicate()
      out = out.decode()
      err = err.decode()
      if process.wait():
        print >> sys.stderr, ("REDUCE returned non-zero exit status: "
                              "See reduce_info.log for more details")
        open('reduce_info.log', 'w').write(err)
      # print out the reduce log even if it worked
      else:
        open('reduce_info.log', 'w').write(err)
      pdbh = StringIO(out)
      recordlist = pdb_read(pdbh, arg_noter, arg_model)
    finally:
      if pdbfile is not sys.stdin:
        pdbfile.close()
  else:
    recordlist = pdb_read(pdbin, arg_noter, arg_model)

  # wrap all atom names to pure standard (always):======================
  recordlist = atom_wrap(recordlist)

  # remove alternate locations and keep only the first one:=============
  if arg_mostpop:
    recordlist = remove_mostpop_altloc(recordlist, filename)
  else:
    recordlist = remove_altloc(recordlist)

  # remove hydrogens if option -y is used:==============================
  if arg_nohyd:
    recordlist = remove_hydrogens(recordlist)

  # find non-standard Amber residues:===================================
  #   TODO: why does the following call discard the return array of
  #         non-standard residue names?
  non_standard(recordlist, filename)
  ns_names = []
  if arg_elbow:
    ns_names = non_standard_elbow(recordlist)

  # keep only protein:==================================================
  if arg_prot:
    recordlist = prot_only(recordlist)

  # remove water if -d option used:=====================================
  if arg_dry:
    recordlist = remove_water(recordlist, filename)

  # renumber atoms and residues:========================================
  recordlist = renumber(recordlist, filename)

  #=====================================================================
  # after this call, residue numbers refer to the ***new*** PDB file
  #=====================================================================

  # find histidines that might have to be changed:=====================
  if arg_constph:
    recordlist = constph(recordlist)
  else:
    recordlist = find_his(recordlist)

  # find possible S-S in the final protein:=============================
  recordlist, cnct, sslist = find_disulfide(recordlist, filename)

  # find possible gaps:==================================================
  gaplist = find_gaps(recordlist)

  # count heavy atoms:==================================================
  find_incomplete(recordlist)

  # =====================================================================
  # make final output to new PDB file
  # =====================================================================
  # pdb_write(recordlist, arg_pdbout, cnct)
  pdb_write(recordlist, arg_pdbout)  # disables printing of CONECT records
  print >> sys.stderr, ""
  sys.stderr = stderr
  return ns_names, gaplist, sslist

#========================================main===========================
if __name__ == "__main__":
  parser = OptionParser(version=__version__)
  parser.add_option("-i", "--in", metavar="FILE", dest="pdbin",
                    help="PDB input file                      (default: stdin)",
                    default='stdin')
  parser.add_option("-o", "--out", metavar="FILE", dest="pdbout",
                    help="PDB output file                     (default: stdout)",
                    default='stdout')
  parser.add_option("-y", "--nohyd", action="store_true", dest="nohyd",
                    help="remove all hydrogen atoms           (default: no)")
  parser.add_option("-d", "--dry", action="store_true", dest="dry",
                    help="remove all water molecules          (default: no)")
  parser.add_option("-p", "--prot", action="store_true", dest="prot",
                    help="keep only Amber-compatible residues (default: no)")
  parser.add_option("--noter", action="store_true", dest="noter",
                    help="remove TER, MODEL, ENDMDL cards     (default: no)")
  parser.add_option("--constantph", action="store_true", dest="constantph",
                    help="rename GLU,ASP,HIS for constant pH simulation")
  parser.add_option("--most-populous", action="store_true", dest="mostpop",
                    help="keep most populous alt. conf. (default is to keep 'A')")
  parser.add_option("--reduce", action="store_true", dest="reduce",
                    help="Run Reduce first to add hydrogens.  (default: no)")
  parser.add_option("--model", type="int", dest="model", default=0,
                    help="Model to use from a multi-model pdb file (integer).  (default: use all models)")
  (opt, args) = parser.parse_args()

  if opt.pdbin == opt.pdbout:
    print >> sys.stderr, "The input and output file names cannot be the same!\n"
    sys.exit(1)

  # Make sure that if we are reading from stdin it's being directed from a pipe
  # or a file. We don't want to wait for user input that will never come.

  if opt.pdbin == 'stdin':
    if os.isatty(sys.stdin.fileno()):
      sys.exit(parser.print_help() or 1)

  run(opt.pdbout, opt.pdbin, opt.nohyd, opt.dry, opt.prot, opt.noter,
      opt.constantph, opt.mostpop, opt.reduce, opt.model)
