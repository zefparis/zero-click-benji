import logging
import time
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List
import re
import argparse
import os
from urllib.parse import urljoin
from datetime import datetime
import tempfile
import shutil
import random
import PyPDF2
from tqdm import tqdm

class FOIAManager:
    def __init__(self, logger: logging.Logger):
        """
        Initializes the FOIAManager with a logger.

        Args:
            logger (logging.Logger): The logger instance to use.
        """
        self.logger = logger
        self.sources = {
            # --- US Government Agencies ---
            "us_fbi": {
                "name": "FBI (United States)",
                "base_url": "https://www.fbi.gov/foia/frequently-requested-records",
                "search_selector": "li.foia-item",
                "title_selector": "a",
                "link_selector": "a",
            },
            "us_cia": {
                "name": "CIA (United States)",
                "base_url": "https://www.cia.gov/readingroom/search",
                "search_selector": "div.search-result",
                "title_selector": "h3.title a",
                "link_selector": "h3.title a",
            },
            "us_nsa": {
                "name": "NSA (United States)",
                "base_url": "https://www.nsa.gov/open/foia/reading-room/",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_nro": {
                "name": "National Reconnaissance Office (NRO)",
                "base_url": "https://www.nro.mil/FOIA/",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_dia": {
                "name": "Defense Intelligence Agency (DIA)",
                "base_url": "https://www.dia.mil/FOIA/",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_dni": {
                "name": "Office of the Director of National Intelligence (DNI)",
                "base_url": "https://www.dni.gov/index.php/foia",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_dod": {
                "name": "Department of Defense (DoD)",
                "base_url": "https://www.dod.mil/foia/",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_pentagon": {
                "name": "The Pentagon",
                "base_url": "https://www.defense.gov/Resources/FOIA/",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_whitehouse": {
                "name": "The White House",
                "base_url": "https://www.whitehouse.gov/briefing-room/foia/",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_state": {
                "name": "Department of State",
                "base_url": "https://www.state.gov/foia/",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_dhs": {
                "name": "Department of Homeland Security (DHS)",
                "base_url": "https://www.dhs.gov/foia",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_justice": {
                "name": "Department of Justice (DOJ)",
                "base_url": "https://www.justice.gov/oip/foia-library",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_treasury": {
                "name": "Department of the Treasury",
                "base_url": "https://home.treasury.gov/policy-issues/freedom-of-information-act",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_energy": {
                "name": "Department of Energy (DOE)",
                "base_url": "https://www.energy.gov/management/office-management/operational-management/freedom-information-act",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_aec": {
                "name": "Atomic Energy Commission (AEC) - Historical",
                "base_url": "https://www.osti.gov/opennet/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Historical records. Now part of DOE.",
            },
            "us_hhs": {
                "name": "Department of Health and Human Services",
                "base_url": "https://www.hhs.gov/foia/index.html",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_va": {
                "name": "Department of Veterans Affairs",
                "base_url": "https://www.va.gov/foia/",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_nasa": {
                "name": "NASA",
                "base_url": "https://www.nasa.gov/FOIA",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_epa": {
                "name": "Environmental Protection Agency (EPA)",
                "base_url": "https://www.epa.gov/foia",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_fec": {
                "name": "Federal Election Commission (FEC)",
                "base_url": "https://www.fec.gov/foia/",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_gsa": {
                "name": "General Services Administration (GSA)",
                "base_url": "https://www.gsa.gov/about-us/contact-us/freedom-of-information-act-foia",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_opm": {
                "name": "Office of Personnel Management (OPM)",
                "base_url": "https://www.opm.gov/about-us/foia-freedom-of-information-act/",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_dot": {
                "name": "Department of Transportation (DOT)",
                "base_url": "https://www.transportation.gov/foia",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_hud": {
                "name": "Department of Housing and Urban Development (HUD)",
                "base_url": "https://www.hud.gov/foia",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_doi": {
                "name": "Department of the Interior (DOI)",
                "base_url": "https://www.doi.gov/foia",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_doc": {
                "name": "Department of Commerce (DOC)",
                "base_url": "https://www.commerce.gov/foia",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_ed": {
                "name": "Department of Education (ED)",
                "base_url": "https://www2.ed.gov/policy/gen/leg/foia/index.html",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_ssa": {
                "name": "Social Security Administration (SSA)",
                "base_url": "https://www.ssa.gov/foia/",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_usps": {
                "name": "United States Postal Service (USPS)",
                "base_url": "https://about.usps.com/who/legal/foia/",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_ntsb": {
                "name": "National Transportation Safety Board (NTSB)",
                "base_url": "https://www.ntsb.gov/legal/foia/Pages/default.aspx",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_fcc": {
                "name": "Federal Communications Commission (FCC)",
                "base_url": "https://www.fcc.gov/foia",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_ftc": {
                "name": "Federal Trade Commission (FTC)",
                "base_url": "https://www.ftc.gov/about-ftc/foia",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_nrc": {
                "name": "Nuclear Regulatory Commission (NRC)",
                "base_url": "https://www.nrc.gov/reading-rm/foia.html",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_cfpb": {
                "name": "Consumer Financial Protection Bureau (CFPB)",
                "base_url": "https://www.consumerfinance.gov/about-us/foia/",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_sba": {
                "name": "Small Business Administration (SBA)",
                "base_url": "https://www.sba.gov/about-sba/sba-performance/open-government/freedom-information-act-foia",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_usaid": {
                "name": "U.S. Agency for International Development (USAID)",
                "base_url": "https://www.usaid.gov/foia",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
             "us_eeoc": {
                "name": "Equal Employment Opportunity Commission (EEOC)",
                "base_url": "https://www.eeoc.gov/foia",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_fdic": {
                "name": "Federal Deposit Insurance Corporation (FDIC)",
                "base_url": "https://www.fdic.gov/resources/foia/",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_ncua": {
                "name": "National Credit Union Administration (NCUA)",
                "base_url": "https://www.ncua.gov/regulation-supervision/foia",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_cftc": {
                "name": "Commodity Futures Trading Commission (CFTC)",
                "base_url": "https://www.cftc.gov/About/FOIA/index.htm",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_sec": {
                "name": "Securities and Exchange Commission (SEC)",
                "base_url": "https://www.sec.gov/foia",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_fhfa": {
                "name": "Federal Housing Finance Agency (FHFA)",
                "base_url": "https://www.fhfa.gov/AboutUs/FOIA/Pages/FOIA.aspx",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_pbgc": {
                "name": "Pension Benefit Guaranty Corporation (PBGC)",
                "base_url": "https://www.pbgc.gov/about/foia",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_uspto": {
                "name": "United States Patent and Trademark Office (USPTO)",
                "base_url": "https://www.uspto.gov/learning-and-resources/open-government/freedom-information-act-foia",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_bls": {
                "name": "Bureau of Labor Statistics (BLS)",
                "base_url": "https://www.bls.gov/foia/",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_census": {
                "name": "Census Bureau",
                "base_url": "https://www.census.gov/about/policies/foia.html",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_bea": {
                "name": "Bureau of Economic Analysis (BEA)",
                "base_url": "https://www.bea.gov/about/foia",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_niosh": {
                "name": "National Institute for Occupational Safety and Health (NIOSH)",
                "base_url": "https://www.cdc.gov/niosh/foia/default.html",
                 "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_osha": {
                "name": "Occupational Safety and Health Administration (OSHA)",
                "base_url": "https://www.osha.gov/foia",
                 "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
             "us_fda": {
                "name": "Food and Drug Administration (FDA)",
                "base_url": "https://www.fda.gov/about-fda/about-foia-office/foia-electronic-reading-room",
                 "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_nih": {
                "name": "National Institutes of Health (NIH)",
                "base_url": "https://www.nih.gov/about-nih/foia",
                 "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_samhsa": {
                "name": "Substance Abuse and Mental Health Services Administration (SAMHSA)",
                "base_url": "https://www.samhsa.gov/about-us/foia",
                 "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_ahrq": {
                "name": "Agency for Healthcare Research and Quality (AHRQ)",
                "base_url": "https://www.ahrq.gov/funding/policies/foia/index.html",
                 "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_cms": {
                "name": "Centers for Medicare & Medicaid Services (CMS)",
                "base_url": "https://www.cms.gov/About-CMS/Agency-Information/FOIA/index",
                 "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_hrsa": {
                "name": "Health Resources and Services Administration (HRSA)",
                "base_url": "https://www.hrsa.gov/about/foia/index.html",
                 "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_ihs": {
                "name": "Indian Health Service (IHS)",
                "base_url": "https://www.ihs.gov/foia/",
                 "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_acl": {
                "name": "Administration for Community Living (ACL)",
                "base_url": "https://acl.gov/about-acl/freedom-information-act-foia",
                 "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_acf": {
                "name": "Administration for Children and Families (ACF)",
                "base_url": "https://www.acf.hhs.gov/foia",
                 "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_onc": {
                "name": "Office of the National Coordinator for Health Information Technology (ONC)",
                "base_url": "https://www.healthit.gov/about-onc/foia",
                 "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_atsdr": {
                "name": "Agency for Toxic Substances and Disease Registry (ATSDR)",
                "base_url": "https://www.atsdr.cdc.gov/foia/index.html",
                 "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            # --- Special Access Programs ---
            "us_sap_jaws": {
                "name": "Joint Worldwide Intelligence Communications System (JWICS)",
                "base_url": "https://www.nsa.gov/open/foia/reading-room/", # Placeholder, actual URL may vary
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Special Access Program. Access may be restricted.",
            },
            "us_sap_umbra": {
                "name": "UMBRA",
                "base_url": "https://www.nsa.gov/open/foia/reading-room/",  # Placeholder, actual URL may vary
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Special Access Program. Access may be restricted.",
            },
            "us_sap_gamma": {
                "name": "GAMMA",
                "base_url": "https://www.nsa.gov/open/foia/reading-room/",  # Placeholder, actual URL may vary
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Special Access Program. Access may be restricted.",
            },
            "us_sap_talentkeyhole": {
                "name": "TALENT KEYHOLE",
                 "base_url": "https://www.nsa.gov/open/foia/reading-room/", # Placeholder, actual URL may vary
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                 "notes": "Special Access Program. Access may be restricted.",
            },
            "us_sap_specialintelligence": {
                "name": "Special Intelligence (SI)",
                "base_url": "https://www.nsa.gov/open/foia/reading-room/", # Placeholder, actual URL may vary
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Special Access Program. Access may be restricted.",
            },
            "us_sap_echelon": {
                "name": "ECHELON",
                "base_url": "https://www.nsa.gov/open/foia/reading-room/", # Placeholder, actual URL may vary
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Special Access Program. Access may be restricted.",
            },
             "us_sap_byeman": {
                "name": "BYEMAN",
                "base_url": "https://www.nsa.gov/open/foia/reading-room/", # Placeholder, actual URL may vary
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Special Access Program. Access may be restricted.",
            },
            "us_sap_comint": {
                "name": "Communications Intelligence (COMINT)",
                "base_url": "https://www.nsa.gov/open/foia/reading-room/", # Placeholder, actual URL may vary
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Special Access Program. Access may be restricted.",
            },
            "us_sap_humint": {
                "name": "Human Intelligence (HUMINT)",
                "base_url": "https://www.nsa.gov/open/foia/reading-room/", # Placeholder, actual URL may vary
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Special Access Program. Access may be restricted.",
            },
            "us_sap_masint": {
                "name": "Measurement and Signature Intelligence (MASINT)",
                "base_url": "https://www.nsa.gov/open/foia/reading-room/", # Placeholder, actual URL may vary
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Special Access Program. Access may be restricted.",
            },
            "us_sap_sigint": {
                "name": "Signals Intelligence (SIGINT)",
                "base_url": "https://www.nsa.gov/open/foia/reading-room/", # Placeholder, actual URL may vary
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Special Access Program. Access may be restricted.",
            },
            "us_sap_geoint": {
                "name": "Geospatial Intelligence (GEOINT)",
                "base_url": "https://www.nsa.gov/open/foia/reading-room/", # Placeholder, actual URL may vary
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Special Access Program. Access may be restricted.",
            },
            "us_sap_osint": {
                "name": "Open Source Intelligence (OSINT)",
                "base_url": "https://www.nsa.gov/open/foia/reading-room/", # Placeholder, actual URL may vary
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Special Access Program. Access may be restricted.",
            },
            "us_sap_tacint": {
                "name": "Tactical Intelligence (TACINT)",
                "base_url": "https://www.nsa.gov/open/foia/reading-room/", # Placeholder, actual URL may vary
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Special Access Program. Access may be restricted.",
            },
            "us_sap_finint": {
                "name": "Financial Intelligence (FININT)",
                "base_url": "https://www.nsa.gov/open/foia/reading-room/", # Placeholder, actual URL may vary
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Special Access Program. Access may be restricted.",
            },
            "us_sap_techint": {
                "name": "Technical Intelligence (TECHINT)",
                "base_url": "https://www.nsa.gov/open/foia/reading-room/", # Placeholder, actual URL may vary
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Special Access Program. Access may be restricted.",
            },
            "us_sap_cbrnint": {
                "name": "Chemical, Biological, Radiological, and Nuclear Intelligence (CBRNINT)",
                "base_url": "https://www.nsa.gov/open/foia/reading-room/", # Placeholder, actual URL may vary
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Special Access Program. Access may be restricted.",
            },
            "us_sap_counterint": {
                "name": "Counterintelligence (CI)",
                "base_url": "https://www.nsa.gov/open/foia/reading-room/", # Placeholder, actual URL may vary
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Special Access Program. Access may be restricted.",
            },
            "us_sap_cyberint": {
                "name": "Cyber Intelligence (CYBINT)",
                "base_url": "https://www.nsa.gov/open/foia/reading-room/", # Placeholder, actual URL may vary
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Special Access Program. Access may be restricted.",
            },
            "us_sap_spaceint": {
                "name": "Space Intelligence (SPACEINT)",
                "base_url": "https://www.nsa.gov/open/foia/reading-room/", # Placeholder, actual URL may vary
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Special Access Program. Access may be restricted.",
            },
            "us_sap_medicalint": {
                "name": "Medical Intelligence (MEDINT)",
                "base_url": "https://www.nsa.gov/open/foia/reading-room/", # Placeholder, actual URL may vary
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Special Access Program. Access may be restricted.",
            },
            "us_sap_allsourceint": {
                "name": "All-Source Intelligence",
                "base_url": "https://www.nsa.gov/open/foia/reading-room/", # Placeholder, actual URL may vary
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Special Access Program. Access may be restricted.",
            },
             "us_sap_aatip": {
                "name": "Advanced Aerospace Threat Identification Program (AATIP)",
                "base_url": "https://www.dod.mil/foia/",  # Placeholder, actual URL may vary
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Special Access Program. Access may be restricted.",
            },
            "us_sap_tencap": {
                "name": "Tactical Exploitation of National Capabilities (TENCAP)",
                "base_url": "https://www.dod.mil/foia/",  # Placeholder, actual URL may vary
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Special Access Program. Access may be restricted.",
            },
            "us_sap_immaculateconstellation": {
                "name": "Immaculate Constellation",
                "base_url": "https://www.dod.mil/foia/",  # Placeholder, actual URL may vary
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Special Access Program. Access may be restricted.",
            },
            # --- Law Enforcement and Security Agencies ---
            "us_secretservice": {
                "name": "Secret Service",
                "base_url": "https://www.secretservice.gov/foia",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_dea": {
                "name": "Drug Enforcement Administration (DEA)",
                "base_url": "https://www.dea.gov/foia",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_fema": {
                "name": "Federal Emergency Management Agency (FEMA)",
                "base_url": "https://www.fema.gov/about/open/foia",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            "us_cdc": {
                "name": "Centers for Disease Control and Prevention (CDC)",
                "base_url": "https://www.cdc.gov/about/foia/index.html",
                "search_selector": "div.item",
                "title_selector": "h3 a",
                "link_selector": "h3 a",
            },
            # --- Military Records and DMV Databases (Public Info Access Points) ---
            "us_military_records": {
                "name": "US Military Records (NARA)",
                "base_url": "https://www.archives.gov/veterans/military-service-records",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Access to military records through NARA.",
            },
             "us_dmv_databases": {
                "name": "US DMV Databases (Public Records)",
                "base_url": "https://www.usa.gov/motor-vehicle-services",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Access to public DMV records varies by state.",
            },
            # --- International Agencies ---
            "uk_mi5": {
                "name": "MI5 (United Kingdom)",
                "base_url": "https://www.mi5.gov.uk/foi",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "UK Security Service.",
            },
            "uk_mi6": {
                "name": "MI6 (United Kingdom)",
                "base_url": "https://www.sis.gov.uk/information/freedom-of-information.html",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "UK Secret Intelligence Service.",
            },
            "ca_csis": {
                "name": "CSIS (Canada)",
                "base_url": "https://www.csis-scrs.gc.ca/en/foia/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Canadian Security Intelligence Service.",
            },
            "au_asio": {
                "name": "ASIO (Australia)",
                "base_url": "https://www.asio.gov.au/freedom-of-information.html",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Australian Security Intelligence Organisation.",
            },
            "de_bfv": {
                "name": "BfV (Germany)",
                "base_url": "https://www.verfassungsschutz.de/en/service/freedom-of-information",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "German Federal Office for the Protection of the Constitution.",
            },
            "fr_dgse": {
                "name": "DGSE (France)",
                "base_url": "https://www.defense.gouv.fr/dgse/dgse/acces-aux-documents-administratifs",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "French Directorate-General for External Security.",
            },
            "il_mossad": {
                "name": "Mossad (Israel)",
                "base_url": "https://www.mossad.gov.il/Eng/About/Pages/ContactUs.aspx",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Israeli Intelligence Agency.",
            },
            "in_raw": {
                "name": "RAW (India)",
                "base_url": "https://www.mea.gov.in/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Indian Intelligence Agency.",
            },
             "cn_mss": {
                "name": "MSS (China)",
                "base_url": "http://www.china.org.cn/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                 "notes": "Chinese Ministry of State Security.",
            },
            "ru_fsb": {
                "name": "FSB (Russia)",
                "base_url": "http://www.fsb.ru/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Russian Federal Security Service.",
            },
            "de_bnd": {
                "name": "BND (Germany)",
                "base_url": "https://www.bnd.bund.de/EN/Service/FreedomOfInformation/freedomofinformation_node.html",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "German Federal Intelligence Service.",
            },
            "ru_svr": {
                "name": "SVR (Russia)",
                "base_url": "https://svr.gov.ru/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Russian Foreign Intelligence Service.",
            },
            "ru_gru": {
                "name": "GRU (Russia)",
                "base_url": "https://structure.mil.ru/structure/forces/main/info.htm",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Russian Military Intelligence.",
            },
            "fr_dgsi": {
                "name": "DGSI (France)",
                 "base_url": "https://www.interieur.gouv.fr/le-ministere/organisation/direction-generale-de-la-securite-interieure-dgsi",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "French General Directorate for Internal Security.",
            },
            "ca_cse": {
                "name": "CSE (Canada)",
                "base_url": "https://www.cse-cst.gc.ca/en/transparency/access-information",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Canadian Communications Security Establishment.",
            },
            "nz_nzsis": {
                "name": "NZSIS (New Zealand)",
                "base_url": "https://www.nzsis.govt.nz/about-us/official-information-act/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "New Zealand Security Intelligence Service.",
            },
            "uk_gchq": {
                "name": "GCHQ (United Kingdom)",
                "base_url": "https://www.gchq.gov.uk/information/freedom-of-information",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "UK Government Communications Headquarters.",
            },
            "es_cni": {
                "name": "CNI (Spain)",
                "base_url": "https://www.inteligencia.gob.es/cni/informacion-publica/acceso-informacion-publica.html",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Spanish National Intelligence Center.",
            },
             "au_asio": {
                "name": "ASIO (Australia)",
                "base_url": "https://www.asio.gov.au/freedom-of-information.html",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Australian Security Intelligence Organisation.",
            },
            "fr_dst": {
                "name": "DST (France)",
                "base_url": "https://www.interieur.gouv.fr/le-ministere/organisation/direction-generale-de-la-securite-interieure-dgsi",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Former French Directorate of Territorial Surveillance (now part of DGSI).",
            },
            "il_shinbet": {
                "name": "Shin Bet (Israel)",
                "base_url": "https://www.shabak.gov.il/Pages/default.aspx",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Israeli Security Agency.",
            },
            "ir_savak": {
                "name": "SAVAK (Iran) - Historical",
                "base_url": "https://www.archives.gov/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Historical Iranian intelligence agency (pre-revolution).",
            },
            "ru_kgb": {
                "name": "KGB (Soviet Union) - Historical",
                "base_url": "https://www.archives.gov/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Historical Soviet intelligence agency.",
            },
            "de_stasi": {
                "name": "Stasi (East Germany) - Historical",
                "base_url": "https://www.bstu.de/en/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Historical East German secret police.",
            },
            "ro_securitate": {
                "name": "Securitate (Romania) - Historical",
                "base_url": "https://www.cnsas.ro/index.html",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Historical Romanian secret police.",
            },
            "pt_pide": {
                "name": "PIDE (Portugal) - Historical",
                "base_url": "https://arquivos.pt/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Historical Portuguese secret police.",
            },
            "cl_dina": {
                "name": "DINA (Chile) - Historical",
                "base_url": "https://www.memoriachilena.gob.cl/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Historical Chilean secret police.",
            },
            # --- International Organizations ---
            "int_interpol": {
                "name": "Interpol",
                "base_url": "https://www.interpol.int/How-we-work/Access-to-information",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "International Criminal Police Organization.",
            },
            "int_europol": {
                "name": "Europol",
                "base_url": "https://www.europol.europa.eu/about-europol/access-to-documents",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "European Union Agency for Law Enforcement Cooperation.",
            },
            "int_un_counterterrorism": {
                "name": "UN Counter-Terrorism",
                "base_url": "https://www.un.org/counterterrorism/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "United Nations Counter-Terrorism Office.",
            },
            "int_nato_publicintel": {
                "name": "NATO Public Intelligence",
                "base_url": "https://www.nato.int/cps/en/natohq/8442.htm",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "NATO Public Intelligence.",
            },
            "int_oas": {
                "name": "Organization of American States (OAS)",
                "base_url": "https://www.oas.org/en/access_information/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Organization of American States.",
            },
            "int_au": {
                "name": "African Union (AU)",
                "base_url": "https://au.int/en/access-information",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "African Union.",
            },
            "int_asean": {
                "name": "Association of Southeast Asian Nations (ASEAN)",
                "base_url": "https://asean.org/access-to-information/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Association of Southeast Asian Nations.",
            },
            "int_sco": {
                "name": "Shanghai Cooperation Organisation (SCO)",
                "base_url": "http://eng.sectsco.org/about_sco/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Shanghai Cooperation Organisation.",
            },
             "int_brics": {
                "name": "BRICS",
                "base_url": "https://www.brics2023.gov.za/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "BRICS cooperation.",
            },
            "int_oecd": {
                "name": "Organisation for Economic Co-operation and Development (OECD)",
                "base_url": "https://www.oecd.org/about/documentaccesspolicy.htm",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Organisation for Economic Co-operation and Development.",
            },
            "int_imf": {
                "name": "International Monetary Fund (IMF)",
                "base_url": "https://www.imf.org/en/about/access-to-information",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "International Monetary Fund.",
            },
            "int_worldbank": {
                "name": "World Bank",
                "base_url": "https://www.worldbank.org/en/access-to-information",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "World Bank.",
            },
            "int_wto": {
                "name": "World Trade Organization (WTO)",
                "base_url": "https://www.wto.org/english/tratop_e/acces_e/acces_e.htm",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "World Trade Organization.",
            },
             "int_icrc": {
                "name": "International Committee of the Red Cross (ICRC)",
                "base_url": "https://www.icrc.org/en/who-we-are/access-information",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "International Committee of the Red Cross.",
            },
            # --- Human Rights and Transparency Organizations ---
            "int_amnesty": {
                "name": "Amnesty International",
                "base_url": "https://www.amnesty.org/en/about-us/access-to-information/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Amnesty International.",
            },
            "int_hrw": {
                "name": "Human Rights Watch",
                "base_url": "https://www.hrw.org/about/our-policies/access-information",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Human Rights Watch.",
            },
            "int_rwb": {
                "name": "Reporters Without Borders",
                "base_url": "https://rsf.org/en/about-us/transparency",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Reporters Without Borders.",
            },
            "int_transparency": {
                "name": "Transparency International",
                "base_url": "https://www.transparency.org/en/who-we-are/access-to-information",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Transparency International.",
            },
            # --- Open Source Intelligence (OSINT) Resources ---
            "osint_globalterrorismdb": {
                "name": "Global Terrorism Database",
                "base_url": "https://www.start.umd.edu/gtd",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Open-source database of terrorist attacks.",
            },
            "osint_osintframework": {
                "name": "OSINT Framework",
                "base_url": "https://osintframework.com/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Framework for OSINT tools and resources.",
            },
            "osint_wikileaks": {
                "name": "WikiLeaks",
                "base_url": "https://wikileaks.org/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Platform for publishing leaked documents.",
            },
            "osint_bellingcat": {
                "name": "Bellingcat",
                "base_url": "https://www.bellingcat.com/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Investigative journalism using OSINT.",
            },
            "osint_icwatch": {
                "name": "ICWatch",
                "base_url": "https://www.icwatch.org/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Intelligence community transparency project.",
            },
            "osint_stratfor": {
                "name": "Stratfor",
                "base_url": "https://stratfor.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Geopolitical intelligence and analysis.",
            },
            "osint_janes": {
                "name": "Janes",
                "base_url": "https://www.janes.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Defense and security intelligence.",
            },
             "osint_sipri": {
                "name": "SIPRI",
                "base_url": "https://www.sipri.org/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Stockholm International Peace Research Institute.",
            },
            "osint_occrp": {
                "name": "Organized Crime and Corruption Reporting Project (OCCRP)",
                "base_url": "https://www.occrp.org/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Investigative journalism focused on organized crime and corruption.",
            },
            "osint_muckrock": {
                "name": "MuckRock",
                "base_url": "https://www.muckrock.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Platform for filing and tracking public records requests.",
            },
            "osint_propublica": {
                "name": "ProPublica",
                "base_url": "https://www.propublica.org/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Investigative journalism in the public interest.",
            },
             "osint_icij": {
                "name": "International Consortium of Investigative Journalists (ICIJ)",
                "base_url": "https://www.icij.org/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Global network of investigative journalists.",
            },
            "osint_forensicarchitecture": {
                "name": "Forensic Architecture",
                "base_url": "https://forensic-architecture.org/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Research agency using architectural techniques for human rights investigations.",
            },
            "osint_shadowproof": {
                "name": "Shadowproof",
                "base_url": "https://shadowproof.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Independent journalism focused on government transparency.",
            },
            "osint_theintercept": {
                "name": "The Intercept",
                "base_url": "https://theintercept.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Investigative journalism focused on national security and civil liberties.",
            },
            "osint_globalwitness": {
                "name": "Global Witness",
                "base_url": "https://www.globalwitness.org/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Investigative journalism focused on corruption and environmental issues.",
            },
            "osint_c4ads": {
                "name": "C4ADS",
                "base_url": "https://www.c4ads.org/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Analysis and data-driven research on conflict and security issues.",
            },
            "osint_recordedfuture": {
                "name": "Recorded Future",
                "base_url": "https://www.recordedfuture.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Threat intelligence platform.",
            },
            "osint_flashpoint": {
                "name": "Flashpoint",
                "base_url": "https://www.flashpoint-intel.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Threat intelligence and risk analysis.",
            },
            "osint_darkowl": {
                 "name": "DarkOwl",
                "base_url": "https://www.darkowl.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Dark web data and intelligence.",
            },
            "osint_maltego": {
                "name": "Maltego",
                "base_url": "https://www.maltego.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Open source intelligence and link analysis tool.",
            },
            "osint_shodan": {
                "name": "Shodan",
                "base_url": "https://www.shodan.io/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Search engine for internet-connected devices.",
            },
            "osint_censys": {
                "name": "Censys",
                "base_url": "https://censys.io/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Internet scanning and security research platform.",
            },
            "osint_zoomeye": {
                "name": "ZoomEye",
                "base_url": "https://www.zoomeye.org/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Cyberspace search engine.",
            },
            "osint_farsightsecurity": {
                "name": "Farsight Security",
                "base_url": "https://www.farsightsecurity.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "DNS intelligence and security data.",
            },
            "osint_domaintools": {
                "name": "DomainTools",
                "base_url": "https://www.domaintools.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Domain name and internet intelligence.",
            },
            "osint_riskiq": {
                "name": "RiskIQ",
                "base_url": "https://www.riskiq.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Digital threat management and security intelligence.",
            },
            "osint_threatconnect": {
                "name": "ThreatConnect",
                "base_url": "https://threatconnect.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Threat intelligence platform.",
            },
            "osint_alienvault": {
                "name": "AlienVault",
                "base_url": "https://www.alienvault.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Unified security management platform.",
            },
            "osint_virustotal": {
                "name": "VirusTotal",
                "base_url": "https://www.virustotal.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Malware analysis and threat intelligence.",
            },
            "osint_hybridanalysis": {
                "name": "Hybrid Analysis",
                "base_url": "https://www.hybrid-analysis.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Malware analysis sandbox.",
            },
            "osint_anyrun": {
                "name": "Any.Run",
                "base_url": "https://any.run/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Interactive malware analysis sandbox.",
            },
            "osint_urlscanio": {
                "name": "URLScan.io",
                "base_url": "https://urlscan.io/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Website scanning and analysis.",
            },
            "osint_waybackmachine": {
                "name": "Wayback Machine",
                "base_url": "https://web.archive.org/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Internet archive.",
            },
            "osint_archivetoday": {
                "name": "Archive.today",
                "base_url": "https://archive.today/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Website archiving service.",
            },
            "osint_googledorks": {
                "name": "Google Dorks",
                "base_url": "https://www.google.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Advanced search queries for Google.",
            },
            "osint_yandexdorks": {
                "name": "Yandex Dorks",
                "base_url": "https://yandex.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Advanced search queries for Yandex.",
            },
            "osint_duckduckgodorks": {
                "name": "DuckDuckGo Dorks",
                "base_url": "https://duckduckgo.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Advanced search queries for DuckDuckGo.",
            },
            "osint_baidudorks": {
                "name": "Baidu Dorks",
                "base_url": "https://www.baidu.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Advanced search queries for Baidu.",
            },
            "osint_bingdorks": {
                "name": "Bing Dorks",
                "base_url": "https://www.bing.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Advanced search queries for Bing.",
            },
            "osint_twitterapi": {
                "name": "Twitter API",
                "base_url": "https://developer.twitter.com/en/docs/twitter-api",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing Twitter data.",
            },
            "osint_facebookgraphapi": {
                "name": "Facebook Graph API",
                "base_url": "https://developers.facebook.com/docs/graph-api",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing Facebook data.",
            },
            "osint_instagramapi": {
                "name": "Instagram API",
                "base_url": "https://developers.facebook.com/docs/instagram-api",
                 "search_selector":  None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing Instagram data.",
            },
            "osint_linkedinapi": {
                "name": "LinkedIn API",
                "base_url": "https://developer.linkedin.com/docs",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing LinkedIn data.",
            },
            "osint_youtubeapi": {
                "name": "YouTube API",
                "base_url": "https://developers.google.com/youtube/v3",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing YouTube data.",
            },
            "osint_redditapi": {
                "name": "Reddit API",
                "base_url": "https://www.reddit.com/dev/api/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing Reddit data.",
            },
            "osint_telegramapi": {
                "name": "Telegram API",
                "base_url": "https://core.telegram.org/api",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing Telegram data.",
            },
            "osint_vkapi": {
                "name": "VK API",
                "base_url": "https://vk.com/dev/api_requests",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing VK data.",
            },
            "osint_tiktokapi": {
                "name": "TikTok API",
                "base_url": "https://developers.tiktok.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing TikTok data.",
            },
            "osint_discordapi": {
                "name": "Discord API",
                "base_url": "https://discord.com/developers/docs/intro",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing Discord data.",
            },
            "osint_githubapi": {
                "name": "GitHub API",
                "base_url": "https://docs.github.com/en/rest",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing GitHub data.",
            },
             "osint_gitlabapi": {
                "name": "GitLab API",
                "base_url": "https://docs.gitlab.com/ee/api/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing GitLab data.",
            },
            "osint_bitbucketapi": {
                "name": "Bitbucket API",
                "base_url": "https://developer.atlassian.com/cloud/bitbucket/rest/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing Bitbucket data.",
            },
            "osint_pastebinapi": {
                "name": "Pastebin API",
                "base_url": "https://pastebin.com/doc_api",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing Pastebin data.",
            },
            "osint_haveibeenpwnedapi": {
                "name": "Have I Been Pwned API",
                "base_url": "https://haveibeenpwned.com/API/v3",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for checking breached accounts.",
            },
            "osint_dehashedapi": {
                "name": "Dehashed API",
                "base_url": "https://www.dehashed.com/api",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing breached data.",
            },
            "osint_intelxapi": {
                "name": "Intelx API",
                "base_url": "https://intelx.io/api",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing data intelligence.",
            },
            "osint_hunterioapi": {
                "name": "Hunter.io API",
                "base_url": "https://hunter.io/api",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for finding email addresses.",
            },
            "osint_clearbitapi": {
                "name": "Clearbit API",
                "base_url": "https://clearbit.com/docs",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for company and person data.",
            },
            "osint_fullcontactapi": {
                "name": "FullContact API",
                "base_url": "https://docs.fullcontact.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for person data.",
            },
            "osint_piplapi": {
                "name": "Pipl API",
                "base_url": "https://pipl.com/api/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for person data.",
            },
            "osint_spokeoapi": {
                "name": "Spokeo API",
                "base_url": "https://www.spokeo.com/api",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for people search.",
            },
            "osint_zabasearchapi": {
                "name": "Zabasearch API",
                "base_url": "https://www.zabasearch.com/api",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for people search.",
            },
            # --- Legal and Financial Databases ---
            "legal_lexisnexis": {
                "name": "LexisNexis",
                "base_url": "https://www.lexisnexis.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Legal research database.",
            },
            "legal_westlaw": {
                "name": "Westlaw",
                "base_url": "https://www.westlaw.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Legal research database.",
            },
            "financial_bloomberglaw": {
                "name": "Bloomberg Law",
                "base_url": "https://www.bloomberglaw.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Legal and financial research database.",
            },
            "financial_factiva": {
                "name": "Factiva",
                "base_url": "https://www.dowjones.com/products/factiva/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                 "notes": "News and business information database.",
            },
            "financial_dowjonesdna": {
                "name": "Dow Jones DNA",
                "base_url": "https://www.dowjones.com/products/dna/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Data and analytics platform.",
            },
            "financial_opencorporates": {
                "name": "OpenCorporates",
                "base_url": "https://opencorporates.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Open database of companies.",
            },
            "financial_opensanctions": {
                "name": "OpenSanctions",
                "base_url": "https://www.opensanctions.org/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Open database of sanctioned entities.",
            },
            "financial_littlesis": {
                "name": "LittleSis",
                "base_url": "https://littlesis.org/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Database of powerful people and organizations.",
            },
            "financial_followthemoney": {
                "name": "FollowTheMoney",
                "base_url": "https://www.followthemoney.org/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Database of campaign finance data.",
            },
            # --- Mapping and Geospatial Resources ---
            "mapping_mapbox": {
                "name": "Mapbox",
                "base_url": "https://www.mapbox.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Mapping and location platform.",
            },
            "mapping_googleearth": {
                "name": "Google Earth",
                "base_url": "https://www.google.com/earth/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Satellite imagery and mapping.",
            },
            "mapping_openstreetmap": {
                "name": "OpenStreetMap",
                "base_url": "https://www.openstreetmap.org/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Open-source mapping data.",
            },
            "mapping_sentinelhub": {
                "name": "Sentinel Hub",
                "base_url": "https://www.sentinel-hub.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Satellite imagery and data.",
            },
            "mapping_planetlabs": {
                "name": "Planet Labs",
                "base_url": "https://www.planet.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Satellite imagery and data.",
            },
            "mapping_maxar": {
                "name": "Maxar Technologies",
                "base_url": "https://www.maxar.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Satellite imagery and data.",
            },
            "mapping_digitalglobe": {
                "name": "DigitalGlobe",
                "base_url": "https://www.digitalglobe.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Satellite imagery and data.",
            },
            "mapping_esri": {
                "name": "Esri",
                "base_url": "https://www.esri.com/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Geographic information system software.",
            },
            "mapping_qgis": {
                "name": "QGIS",
                "base_url": "https://www.qgis.org/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Open-source geographic information system software.",
            },
            "mapping_grassgis": {
                "name": "GRASS GIS",
                "base_url": "https://grass.osgeo.org/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Open-source geographic information system software.",
            },
            "mapping_arcgis": {
                "name": "ArcGIS",
                "base_url": "https://www.esri.com/en-us/arcgis/products/arcgis-platform/overview",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Geographic information system software.",
            },
             "mapping_geojson": {
                "name": "GeoJSON",
                "base_url": "https://geojson.org/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Format for encoding geographic data structures.",
            },
            "mapping_kml": {
                "name": "KML",
                "base_url": "https://developers.google.com/kml/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Format for encoding geographic data structures.",
            },
            "mapping_shapefile": {
                "name": "Shapefile",
                "base_url": "https://www.esri.com/en-us/arcgis/about-arcgis/overview",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Geospatial vector data format.",
            },
            "mapping_geotiff": {
                "name": "GeoTIFF",
                "base_url": "https://www.remotesensing.org/geotiff/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Geospatial raster data format.",
            },
            "mapping_georss": {
                "name": "GeoRSS",
                "base_url": "https://www.georss.org/",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Geospatial extension to RSS feeds.",
            },
            "mapping_wms": {
                "name": "WMS",
                "base_url": "https://www.ogc.org/standards/wms",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Web Map Service.",
            },
            "mapping_wfs": {
                "name": "WFS",
                "base_url": "https://www.ogc.org/standards/wfs",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Web Feature Service.",
            },
            "mapping_tms": {
                "name": "TMS",
                "base_url": "https://wiki.osgeo.org/wiki/Tile_Map_Service_Specification",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Tile Map Service.",
            },
            "mapping_wmts": {
                "name": "WMTS",
                "base_url": "https://www.ogc.org/standards/wmts",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Web Map Tile Service.",
            },
            "osint_instagramapi": {
                "name": "Instagram API",
                "base_url": "https://developers.facebook.com/docs/instagram-api/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing Instagram data.",
            },
            "osint_linkedinapi": {
                "name": "LinkedIn API",
                "base_url": "https://developer.linkedin.com/docs",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing LinkedIn data.",
            },
            "osint_youtubeapi": {
                "name": "YouTube API",
                "base_url": "https://developers.google.com/youtube/v3",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing YouTube data.",
            },
            "osint_redditapi": {
                "name": "Reddit API",
                "base_url": "https://www.reddit.com/dev/api/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing Reddit data.",
            },
            "osint_telegramapi": {
                "name": "Telegram API",
                "base_url": "https://core.telegram.org/api",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing Telegram data.",
            },
            "osint_vkapi": {
                "name": "VK API",
                "base_url": "https://vk.com/dev/api_requests",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing VK data.",
            },
            "osint_tiktokapi": {
                "name": "TikTok API",
                "base_url": "https://developers.tiktok.com/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing TikTok data.",
            },
            "osint_discordapi": {
                "name": "Discord API",
                "base_url": "https://discord.com/developers/docs/intro",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing Discord data.",
            },
            "osint_githubapi": {
                "name": "GitHub API",
                "base_url": "https://docs.github.com/en/rest",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing GitHub data.",
            },
            "osint_gitlabapi": {
                "name": "GitLab API",
                "base_url": "https://docs.gitlab.com/ee/api/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing GitLab data.",
            },
            "osint_bitbucketapi": {
                "name": "Bitbucket API",
                "base_url": "https://developer.atlassian.com/cloud/bitbucket/rest/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing Bitbucket data.",
            },
            "osint_pastebinapi": {
                "name": "Pastebin API",
                "base_url": "https://pastebin.com/doc_api",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing Pastebin data.",
            },
            "osint_haveibeenpwnedapi": {
                "name": "Have I Been Pwned API",
                "base_url": "https://haveibeenpwned.com/API/v3",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for checking breached accounts.",
            },
            "osint_dehashedapi": {
                "name": "Dehashed API",
                "base_url": "https://www.dehashed.com/api",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing breached data.",
            },
            "osint_intelxapi": {
                "name": "Intelx API",
                "base_url": "https://intelx.io/api",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for accessing data intelligence.",
            },
            "osint_hunterioapi": {
                "name": "Hunter.io API",
                "base_url": "https://hunter.io/api",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for finding email addresses.",
            },
            "osint_clearbitapi": {
                "name": "Clearbit API",
                "base_url": "https://clearbit.com/docs",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for company and person data.",
            },
            "osint_fullcontactapi": {
                "name": "FullContact API",
                "base_url": "https://docs.fullcontact.com/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for person data.",
            },
            "osint_piplapi": {
                "name": "Pipl API",
                "base_url": "https://pipl.com/api/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for person data.",
            },
            "osint_spokeoapi": {
                "name": "Spokeo API",
                "base_url": "https://www.spokeo.com/api",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for people search.",
            },
            "osint_zabasearchapi": {
                "name": "Zabasearch API",
                "base_url": "https://www.zabasearch.com/api",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "API for people search.",
            },
            "legal_lexisnexis": {
                "name": "LexisNexis",
                "base_url": "https://www.lexisnexis.com/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Legal research database.",
            },
            "legal_westlaw": {
                "name": "Westlaw",
                "base_url": "https://www.westlaw.com/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Legal research database.",
            },
            "financial_bloomberglaw": {
                "name": "Bloomberg Law",
                "base_url": "https://www.bloomberglaw.com/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Legal and financial research database.",
            },
            "financial_factiva": {
                "name": "Factiva",
                "base_url": "https://www.dowjones.com/products/factiva/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "News and business information database.",
            },
            "financial_dowjonesdna": {
                "name": "Dow Jones DNA",
                "base_url": "https://www.dowjones.com/products/dna/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Data and analytics platform.",
            },
            "financial_opencorporates": {
                "name": "OpenCorporates",
                "base_url": "https://opencorporates.com/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Open database of companies.",
            },
            "financial_opensanctions": {
                "name": "OpenSanctions",
                "base_url": "https://www.opensanctions.org/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Open database of sanctioned entities.",
            },
            "financial_littlesis": {
                "name": "LittleSis",
                "base_url": "https://littlesis.org/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Database of powerful people and organizations.",
            },
            "financial_followthemoney": {
                "name": "FollowTheMoney",
                "base_url": "https://www.followthemoney.org/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Database of campaign finance data.",
            },
            "mapping_mapbox": {
                "name": "Mapbox",
                "base_url": "https://www.mapbox.com/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Mapping and location platform.",
            },
            "mapping_googleearth": {
                "name": "Google Earth",
                "base_url": "https://www.google.com/earth/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Satellite imagery and mapping.",
            },
            "mapping_openstreetmap": {
                "name": "OpenStreetMap",
                "base_url": "https://www.openstreetmap.org/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Open-source mapping data.",
            },
            "mapping_sentinelhub": {
                "name": "Sentinel Hub",
                "base_url": "https://www.sentinel-hub.com/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Satellite imagery and data.",
            },
            "mapping_planetlabs": {
                "name": "Planet Labs",
                "base_url": "https://www.planet.com/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Satellite imagery and data.",
            },
            "mapping_maxar": {
                "name": "Maxar Technologies",
                "base_url": "https://www.maxar.com/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Satellite imagery and data.",
            },
            "mapping_digitalglobe": {
                "name": "DigitalGlobe",
                "base_url": "https://www.digitalglobe.com/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Satellite imagery and data.",
            },
            "mapping_esri": {
                "name": "Esri",
                "base_url": "https://www.esri.com/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Geographic information system software.",
            },
            "mapping_qgis": {
                "name": "QGIS",
                "base_url": "https://www.qgis.org/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Open-source geographic information system software.",
            },
            "mapping_grassgis": {
                "name": "GRASS GIS",
                "base_url": "https://grass.osgeo.org/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Open-source geographic information system software.",
            },
            "mapping_arcgis": {
                "name": "ArcGIS",
                "base_url": "https://www.esri.com/en-us/arcgis/products/arcgis-platform/overview",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Geographic information system software.",
            },
            "mapping_geojson": {
                "name": "GeoJSON",
                "base_url": "https://geojson.org/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Format for encoding geographic data structures.",
            },
            "mapping_kml": {
                "name": "KML",
                "base_url": "https://developers.google.com/kml/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Format for encoding geographic data structures.",
            },
            "mapping_shapefile": {
                "name": "Shapefile",
                "base_url": "https://www.esri.com/en-us/arcgis/about-arcgis/overview",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Geospatial vector data format.",
            },
            "mapping_geotiff": {
                "name": "GeoTIFF",
                "base_url": "https://www.remotesensing.org/geotiff/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Geospatial raster data format.",
            },
            "mapping_georss": {
                "name": "GeoRSS",
                "base_url": "https://www.georss.org/",
                "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Geospatial extension to RSS feeds.",
            },
            "mapping_wms": {
                "name": "WMS",
                "base_url": "https://www.ogc.org/standards/wmts",
                 "search_selector": None,
                "title_selector": None,
                "link_selector": None,
                "notes": "Web Map Tile Service.",
            },
        }

    def scrape_foia_documents(self, source_id: str) -> List[Dict[str, Any]]:
        """
        Scrapes FOIA documents from a specified source.

        Args:
            source_id (str): The ID of the source to scrape from.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing document information.
        """
        if source_id not in self.sources:
            self.logger.error(f"Invalid source ID: {source_id}")
            return []

        source = self.sources[source_id]
        documents = []

        if source["search_selector"] is None:
            self.logger.warning(f"Skipping {source['name']} due to no search selector.")
            return []

        try:
            response = requests.get(source["base_url"])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.select(source["search_selector"])

            for item in items:
                try:
                    title_element = item.select_one(source["title_selector"])
                    link_element = item.select_one(source["link_selector"])
                    
                    if title_element and link_element:
                        title = title_element.get_text(strip=True)
                        link = link_element.get('href', '')
                        
                        if not link.startswith('http'):
                            link = urljoin(source["base_url"], link)

                        documents.append({
                            'title': title,
                            'url': link,
                            'source': source["name"]
                        })
                except Exception as e:
                    self.logger.error(f"Error parsing document from {source_id}: {str(e)}")
                    continue

            self.logger.info(f"Successfully scraped {len(documents)} documents from {source['name']}")
            return documents

        except requests.RequestException as e:
            self.logger.error(f"Error fetching documents from {source['name']}: {str(e)}")
            return []

    def search_documents(self, documents: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Searches through documents for a specific query.

        Args:
            documents (List[Dict[str, Any]]): List of documents to search through.
            query (str): Search query string.

        Returns:
            List[Dict[str, Any]]: Filtered list of documents matching the query.
        """
        query = query.lower()
        results = []

        for doc in documents:
            if query in doc['title'].lower():
                results.append(doc)

        self.logger.info(f"Found {len(results)} documents matching query: {query}")
        return results

    def download_document(self, url: str, output_path: str) -> bool:
        """
        Downloads a document from a given URL.

        Args:
            url (str): URL of the document to download.
            output_path (str): Path where the document should be saved.

        Returns:
            bool: True if download was successful, False otherwise.
        """
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            self.logger.info(f"Successfully downloaded document to {output_path}")
            return True

        except (requests.RequestException, IOError) as e:
            self.logger.error(f"Error downloading document: {str(e)}")
            return False

    def download_and_extract_pdf_text(self, url: str, output_dir: str) -> str:
        """
        Downloads a PDF document from a given URL, extracts text content, and saves it to a text file.

        Args:
            url (str): URL of the PDF document to download.
            output_dir (str): Directory where the extracted text file should be saved.

        Returns:
            str: Path to the saved text file if successful, None otherwise.
        """
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            # Create a temporary file to store the downloaded PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        tmp_file.write(chunk)
                temp_pdf_path = tmp_file.name

            # Extract text from PDF
            text_content = self._extract_text_from_pdf(temp_pdf_path)

            # Create a unique filename for the text file
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            random_id = random.randint(1000, 9999)
            filename = f"extracted_text_{timestamp}_{random_id}.txt"
            output_path = os.path.join(output_dir, filename)

            # Save the extracted text to a file
            with open(output_path, 'w', encoding='utf-8') as text_file:
                text_file.write(text_content)

            # Clean up the temporary PDF file
            os.unlink(temp_pdf_path)

            self.logger.info(f"Successfully downloaded and extracted text from {url} to {output_path}")
            return output_path

        except (requests.RequestException, IOError, PyPDF2.errors.PdfReadError) as e:
            self.logger.error(f"Error downloading or extracting text from {url}: {str(e)}")
            return None

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extracts text content from a PDF file.

        Args:
            pdf_path (str): Path to the PDF file.

        Returns:
            str: Extracted text content.
        """
        text = ""
        try:
            with open(pdf_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
        except Exception as e:
             self.logger.error(f"Error extracting text from PDF {pdf_path}: {str(e)}")
        return text

    def process_documents(self, source_id: str, query: str = None, output_dir: str = None, download_all: bool = False):
        """
        Processes documents from a specified source, optionally searching, downloading, and extracting text.

        Args:
            source_id (str): The ID of the source to process.
            query (str, optional): Search query string. Defaults to None.
            output_dir (str, optional): Directory to save downloaded documents. Defaults to None.
            download_all (bool, optional): If True, downloads all documents, otherwise only matching ones. Defaults to False.
        """
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        documents = self.scrape_foia_documents(source_id)
        if not documents:
            self.logger.warning(f"No documents found for source: {source_id}")
            return

        if query:
            documents = self.search_documents(documents, query)
            if not documents:
                self.logger.warning(f"No documents found matching query: {query}")
                return

        if download_all:
            docs_to_process = documents
        else:
             docs_to_process = documents if query else []

        if docs_to_process:
            self.logger.info(f"Processing {len(docs_to_process)} documents...")
            for doc in tqdm(docs_to_process, desc="Downloading and Extracting Documents"):
                try:
                    file_extension = os.path.splitext(doc['url'])[1].lower()
                    if file_extension == '.pdf':
                        if output_dir:
                            self.download_and_extract_pdf_text(doc['url'], output_dir)
                        else:
                            self.logger.warning(f"Output directory not specified, skipping PDF extraction for: {doc['title']}")
                    else:
                        if output_dir:
                            filename = os.path.basename(doc['url'])
                            output_path = os.path.join(output_dir, filename)
                            self.download_document(doc['url'], output_path)
                        else:
                            self.logger.warning(f"Output directory not specified, skipping download for: {doc['title']}")
                except Exception as e:
                    self.logger.error(f"Error processing document {doc['title']}: {str(e)}")
                    continue
        else:
            self.logger.info("No documents to download or extract.")

def main():
    parser = argparse.ArgumentParser(description="Scrape, search, and download FOIA documents.")
    parser.add_argument("source_id", help="The ID of the source to scrape from.")
    parser.add_argument("-q", "--query", help="Search query string.", default=None)
    parser.add_argument("-o", "--output_dir", help="Directory to save downloaded documents.", default=None)
    parser.add_argument("-a", "--all", help="Download all documents, not just matching ones.", action="store_true")
    parser.add_argument("-l", "--log_level", help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).", default="INFO")

    args = parser.parse_args()

    # Set up logging
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    foia_manager = FOIAManager(logger)
    foia_manager.process_documents(args.source_id, args.query, args.output_dir, args.all)

if __name__ == "__main__":
    main()