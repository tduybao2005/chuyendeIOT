"""
CAU HINH SERVER - doc tu bien moi truong hoac file .env.

=========================================================================
KHONG CO MAT KHAU NAO NAM TRONG FILE .py CUA THU MUC NAY.
=========================================================================
Repo nay la repo cong khai tren GitHub. Connection string cua MongoDB Atlas
co san user + mat khau ben trong, con API_KEY la thu duy nhat chan nguoi la
ghi bay vao Database. Viet thang vao file .py la day ca hai len GitHub.

Bot quet GitHub tim connection string la chuyen co that va rat nhanh - Atlas
con tu gui canh bao khi phat hien key cua minh bi lo cong khai. Vi vay:

    .env          <- chua gia tri THAT, da bi .gitignore chan (dong '.env*')
    .env.example  <- chi chua cho trong, day la file duoc commit

Cach dien: copy .env.example thanh .env roi dien vao. Xem HUONG_DAN_ATLAS.md.
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Do dai toi thieu cua API_KEY.
#
# Khoa ngan nhu "abc" thi do bang tay vai giay la ra, co cung nhu khong. 16
# ky tu ngau nhien la du xa tam do voi mot bai thuc hanh. Lenh tao khoa tot:
#     python -c "import secrets; print(secrets.token_urlsafe(32))"
DO_DAI_API_KEY_TOI_THIEU = 16


class CauHinh(BaseSettings):
    """Toan bo cau hinh server. Thieu thu bat buoc thi bao loi NGAY luc khoi dong.

    Bao loi som la co y: neu de server khoi dong duoc voi cau hinh thieu thi
    no trong nhu dang chay binh thuong, den luc bam demo truoc lop moi loi -
    luc do khong con thoi gian sua.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",          # bo qua bien la trong .env, khong bao loi
        case_sensitive=False,    # MONGODB_URI hay mongodb_uri deu duoc
    )

    # --- Bat buoc dien (khong co gia tri mac dinh) ---
    mongodb_uri: str = Field(
        description="Connection string cua MongoDB Atlas (mongodb+srv://...)",
    )
    api_key: str = Field(
        description="Khoa bao mat; client phai gui kem moi request",
    )

    # --- Co san mac dinh, doi duoc neu muon ---
    mongodb_db: str = Field(
        default="iot_buoi8",
        description="Ten database trong Atlas",
    )
    mongodb_collection: str = Field(
        default="du_lieu_cam_bien",
        description="Ten collection luu cac ban ghi",
    )
    host: str = Field(
        default="0.0.0.0",
        description="Dia chi lang nghe. Phai la 0.0.0.0 chu KHONG phai "
                    "127.0.0.1, neu khong Raspberry Pi o may khac khong goi "
                    "toi duoc - chi chinh may chay server moi vao duoc.",
    )
    port: int = Field(default=8000, ge=1, le=65535)

    @field_validator("mongodb_uri")
    @classmethod
    def _kiem_tra_dang_uri(cls, uri: str) -> str:
        uri = uri.strip()
        if not uri.startswith(("mongodb://", "mongodb+srv://")):
            raise ValueError(
                "MONGODB_URI phai bat dau bang 'mongodb+srv://' (Atlas) hoac "
                "'mongodb://' (Mongo chay tren may). Xem HUONG_DAN_ATLAS.md."
            )
        return uri

    @field_validator("api_key")
    @classmethod
    def _kiem_tra_do_dai_khoa(cls, khoa: str) -> str:
        khoa = khoa.strip()
        if len(khoa) < DO_DAI_API_KEY_TOI_THIEU:
            raise ValueError(
                f"API_KEY phai dai it nhat {DO_DAI_API_KEY_TOI_THIEU} ky tu. "
                'Tao khoa tot: python -c "import secrets; '
                'print(secrets.token_urlsafe(32))"'
            )
        return khoa


def doc_cau_hinh() -> CauHinh:
    """Doc cau hinh, bao loi de hieu neu thieu.

    Khong dung lru_cache: server chi goi ham nay dung mot lan luc khoi dong,
    con test can doc lai nhieu lan voi bien moi truong khac nhau. Cache o day
    chi lam test dinh vao nhau ma khong nhanh them duoc gi.
    """
    return CauHinh()
