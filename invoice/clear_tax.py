import os
import config
import requests
import shutil
import simplejson as json
from datetime import datetime
from inboicing_system.settings import logger
from .utils import generate_cleartax_data, generate_ewaybill_data

# from communication.s3_upload import s3_upload_file


def generate_irn(invoice):
    einvoice_data = generate_cleartax_data(invoice)

    headers = {
        "Content-Type": "application/json",
        "x-cleartax-auth-token": config.CLEARTAX_PROD_AUTH,
        "gstin": invoice.seller.gstin,
    }

    url = f"{config.CLEARTAX_PROD_HOSTNAME}{config.CLEARTAX_IRN_URL}"
    response = requests.put(url, data=einvoice_data, headers=headers)

    if response.status_code > 200:
        logger.error(
            f"GENERATE IRN: Not generated IRN for {invoice.invoice_number} ERROR: {response.json()}"
        )
        return None
    else:
        logger.info(f"GENERATE IRN: CLEARTAX RESPONSE {response.json()}")
        response_data = response.json()[0]
        if response_data.get("document_status") == "IRN_GENERATED":
            logger.info(f"GENERATE IRN: {response_data.get('document_status')}")
            govt_response = response_data.get("govt_response")
            if govt_response.get("Success") == "Y":
                logger.info(f"GENERATE IRN: Status -> {govt_response.get('Success')}")
                irn = govt_response.get("Irn")
                invoice.irn = irn
                invoice.save()
                return irn
            elif govt_response.get("Success") == "N":
                logger.info(
                    f"GENERATE IRN: Something went wrong while generating INR for {invoice.invoice_number} ERROR: {govt_response.get('ErrorDetails')}"
                )
        return None


def download_e_invoice(irn, gstin):
    headers = {"x-cleartax-auth-token": config.CLEARTAX_PROD_AUTH, "gstin": gstin}

    url = f"{config.CLEARTAX_PROD_HOSTNAME}{config.CLEARTAX_E_INVOICE_DOWNLOAD}?irns={irn}&template=6e351b87-35b4-48a5-bc5f-d085685410f7"

    response = requests.get(url, headers=headers, stream=True)

    current_date = datetime.now()
    file_name = f"{irn}.pdf"
    file_path = os.path.join(
        "/b2b-invoices",
        str(current_date.year),
        str(current_date.month),
        str(current_date.day),
    )

    file_url = os.path.join(file_path, file_name)
    tmp_path = "/tmp" + file_path
    os.makedirs(tmp_path, exist_ok=True)
    tmp_file_path = "/tmp" + file_url

    with open(tmp_file_path, "wb") as out_file:
        shutil.copyfileobj(response.raw, out_file)

    # s3_file_obj = s3_upload_file(tmp_file_path, remove_tmp=True)
    # if os.path.exists(tmp_file_path):
    #     os.remove(tmp_file_path)
    # return s3_file_obj["file_path"]


def generate_ewaybill(invoice):
    ewaybill_data = generate_ewaybill_data(invoice)

    headers = {
        "Content-Type": "application/json",
        "x-cleartax-auth-token": config.CLEARTAX_PROD_AUTH,
        "gstin": invoice.seller.gstin,
    }

    url = f"{config.CLEARTAX_PROD_HOSTNAME}{config.CLEARTAX_EWAYBILL_URL}"
    response = requests.post(url, data=ewaybill_data, headers=headers)

    if response.status_code > 200:
        logger.error(
            f"GENERATE EWAYBILL: Something went wrong while generating EWB for {invoice.invoice_number} ERROR: {response.json()}"
        )
        return None
    else:
        logger.info(f"GENERATE EWAYBILL: CLEARTAX RESPONSE {response.json()}")
        response_data = response.json()[0]
        if response_data.get("ewb_status") == "GENERATED":
            logger.info(f"GENERATE EWAYBILL: {response_data.get('ewb_status')}")
            govt_response = response_data.get("govt_response")
            if govt_response.get("Success") == "Y":
                logger.info(
                    f"GENERATE EWAYBILL: Status -> {govt_response.get('Success')}"
                )
                ewb_no = govt_response.get("EwbNo")
                invoice.ewb_number = ewb_no
                invoice.save()
                return ewb_no
            elif govt_response.get("Success") == "N":
                logger.info(
                    f"GENERATE EWAYBILL: Something went wrong while generating INR for {invoice.invoice_number} ERROR: {govt_response.get('ErrorDetails')}"
                )
        return None


def download_ewaybill(ewb_no, gstin):
    headers = {
        "Content-Type": "application/json",
        "x-cleartax-auth-token": config.CLEARTAX_PROD_AUTH,
        "gstin": gstin,
    }

    url = f"{config.CLEARTAX_PROD_HOSTNAME}{config.CLEARTAX_EWAYBILL_DOWNLOAD}"

    data = {"format": "PDF", "ewb_numbers": [ewb_no], "print_type": "DETAILED"}
    data = json.dumps(data)
    response = requests.post(url, data=data, headers=headers)

    current_date = datetime.now()
    file_name = f"{ewb_no}.zip"
    file_path = os.path.join(
        "/b2b-invoices",
        str(current_date.year),
        str(current_date.month),
        str(current_date.day),
    )

    file_url = os.path.join(file_path, file_name)
    tmp_path = "/tmp" + file_path
    os.makedirs(tmp_path, exist_ok=True)
    tmp_file_path = "/tmp" + file_url

    with open(tmp_file_path, "wb") as out_file:
        out_file.write(response.content)
    return tmp_file_path

    # s3_file_obj = s3_upload_file(tmp_file_path, remove_tmp=True)
    # if os.path.exists(tmp_file_path):
    #     os.remove(tmp_file_path)
    # return s3_file_obj["file_path"]
