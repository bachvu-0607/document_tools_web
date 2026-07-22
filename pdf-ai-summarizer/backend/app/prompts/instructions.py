SUMMARY_TYPE_INSTRUCTIONS: dict[str, str] = {
    "short": "Tom tat that ngan gon, chi giu lai dung y chinh cot loi nhat, khong di vao chi tiet phu.",
    "detailed": "Tom tat day du, giai thich ro rang tung phan noi dung, khong bo sot y quan trong nao.",
    "bullet": "Trinh bay duoi dang danh sach gach dau dong ngan gon, de doc luot, moi gach dau dong 1 y.",
    "study_notes": "Trinh bay nhu ghi chu hoc tap: chia tieu de ro rang cho tung phan, giai thich thuat ngu kho, de xem lai nhanh truoc ky thi.",
    "executive": "Tom tat sup tich kieu 'executive summary', di thang vao trong tam, phu hop cho nguoi ban ron chi co vai phut de nam noi dung.",
    "qa": "Trinh bay duoi dang cac cap cau hoi - tra loi bam sat noi dung tai lieu, giup nguoi doc tu kiem tra lai kien thuc.",
}

AUDIENCE_INSTRUCTIONS: dict[str, str] = {
    "student": "nguoi hoc dang tim hieu kien thuc nen, can giai thich de hieu, khong gia dinh nguoi doc da biet truoc nhieu.",
    "beginner": "nguoi hoan toan moi voi chu de nay, can giai thich tu nhung khai niem co ban nhat, tranh dung thuat ngu chuyen mon neu khong giai thich kem.",
    "developer": "nguoi co nen tang ky thuat, co the dung thuat ngu chuyen nganh, uu tien do chinh xac ky thuat hon la giai thich lai kien thuc co ban.",
    "teacher": "nguoi se dung noi dung nay de giang day lai cho nguoi khac, can cau truc ro rang theo tung phan, de trich dan lai.",
    "professional": "nguoi da co kinh nghiem lam viec trong nganh, can thong tin sup tich, khong can giai thich lai kien thuc nen.",
    "researcher": "nguoi doc theo huong hoc thuat/nghien cuu, can giu lai tinh chinh xac, neu ro so lieu va phuong phap khi co trong tai lieu goc.",
}

FOCUS_INSTRUCTIONS: dict[str, str] = {
    "exam": "Tap trung liet ke cac khai niem, dinh nghia, cong thuc quan trong nhat co kha nang xuat hien trong bai kiem tra. Cuoi moi phan, goi y 1-2 cau hoi on tap ngan.",
    "concepts": "Giai thich ro cac khai niem cot loi, dinh nghia thuat ngu quan trong, va moi lien he giua cac y chinh.",
    "examples": "Uu tien giu lai va giai thich cac vi du, doan code, tinh huong minh hoa cu the co trong tai lieu.",
    "key_data": "Trich xuat va nhan manh cac so lieu, thong ke, con so quan trong nhat trong tai lieu.",
    "conclusions": "Tap trung vao phan ket luan, khuyen nghi, va cac hanh dong duoc de xuat trong tai lieu.",
    "methodology": "Tom tat ro phuong phap, quy trinh, cach tiep can duoc su dung trong tai lieu.",
    "pros_cons": "Phan tich ro uu diem, han che, va danh gia phan bien ve noi dung trong tai lieu.",
}

TONE_INSTRUCTIONS: dict[str, str] = {
    "formal": "dung van phong trang trong, chuyen nghiep, chuan muc.",
    "friendly": "dung van phong gan gui, de hieu, nhu dang giai thich cho ban be.",
    "academic": "dung van phong hoc thuat, chinh xac ve thuat ngu, phu hop bao cao/nghien cuu.",
}
