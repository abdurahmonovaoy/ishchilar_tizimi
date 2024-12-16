from django.db import models
from datetime import datetime
from datetime import date

class Lavozim(models.Model):
    nomi = models.CharField(max_length=100, verbose_name="Lavozim nomi")

    class Meta:
        verbose_name = "Lavozim"
        verbose_name_plural = "Lavozimlar"

    def __str__(self):
        return self.nomi


class Ishchi(models.Model):
    JINSI_TANLOVLARI = (
        ('Erkak', 'Erkak'),
        ('Ayol', 'Ayol'),
    )

    ism = models.CharField(max_length=50, verbose_name="Ism")
    familiya = models.CharField(max_length=50, verbose_name="Familiya")
    tugilgan_sana = models.DateField(verbose_name="Tug‘ilgan sana")
    jinsi = models.CharField(max_length=10, choices=JINSI_TANLOVLARI, verbose_name="Jinsi")
    telefon = models.CharField(max_length=15, verbose_name="Telefon raqami")
    lavozim = models.ForeignKey(Lavozim, on_delete=models.SET_NULL, null=True, verbose_name="Lavozim")  # ForeignKey qo'shildi
    ishga_kirgan_sana = models.DateField(default=date.today, verbose_name="Ishga kirgan sana")

    class Meta:
        verbose_name = "Ishchi"
        verbose_name_plural = "Ishchilar"

    @property
    def yosh(self):
        """Tug‘ilgan sanadan yoshni avtomatik hisoblaydi."""
        today = date.today()
        return today.year - self.tugilgan_sana.year - ((today.month, today.day) < (self.tugilgan_sana.month, self.tugilgan_sana.day))

    def __str__(self):
        return f"{self.ism} {self.familiya}"


class IshVaqti(models.Model):
    ishchi = models.ForeignKey(Ishchi, on_delete=models.CASCADE, related_name="ish_vaqtlari")
    kun = models.DateField()
    boshlanish_vaqti = models.TimeField()
    tugash_vaqti = models.TimeField()

    def __str__(self):
        return f"{self.ishchi} - {self.kun}"

    def ish_soati(self):
        """Ish soatini hisoblaydi"""
        boshlanish = datetime.combine(datetime.min, self.boshlanish_vaqti)
        tugash = datetime.combine(datetime.min, self.tugash_vaqti)
        vaqt_farki = tugash - boshlanish
        return vaqt_farki.total_seconds() / 3600  # Soatlarga o‘girish

    class Meta:
        verbose_name = "Ish vaqti"
        verbose_name_plural = "Ish vaqtlar"


class IshHaqqi(models.Model):
    ishchi = models.ForeignKey(Ishchi, on_delete=models.CASCADE, related_name='ish_haqqi')
    oy = models.DateField(verbose_name="Oy")  # DateField o'zgartirildi
    jami_ish_soati = models.FloatField(default=0.0, verbose_name="Jami ish soati")
    tarif = models.FloatField(default=0.0, verbose_name="Tarif (soatlik)")
    jami_ish_haqi = models.FloatField(default=0.0, verbose_name="Jami ish haqi")

    class Meta:
        verbose_name = "Ish haqi"
        verbose_name_plural = "Ish haqlari"

    def save(self, *args, **kwargs):
        """Jami ish haqini avtomatik hisoblaydi."""
        self.jami_ish_haqi = self.jami_ish_soati * self.tarif
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ishchi} - {self.oy}"  # Ishchi va oyni ko'rsatish
