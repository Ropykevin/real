from flask import Flask, render_template, redirect, url_for, request, jsonify, json, session, abort, make_response, flash
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
from authlib.common.security import generate_token
import requests
import os
import logging
from functools import wraps
import firebase_admin
from firebase_admin import credentials, auth, exceptions
