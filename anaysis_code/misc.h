Int_t ascii_to_binary(Int_t num)
{
  Int_t open_channels=0;

  for(Int_t bit=15;bit>=0;bit--)
   if(num&(1<<bit))
   {
     open_channels++;
   }

  return open_channels;
}

UInt_t File_Size(FILE *raw)
{
  long pointer_position;
  UInt_t file_size0;
  pointer_position=ftell(raw);
  fseek(raw,0,SEEK_END);
  file_size0=ftell(raw);
  file_size0=file_size0/1024/1024;
  fseek(raw,pointer_position,SEEK_SET);
  
  return file_size0;
}

void Get_Name(char *name, char *filename)
{
    unsigned int len = strlen(filename);
    int start_count = 0;
    int end_count = 0;

    for(unsigned int i=0;i<len;i++)
    {
        if(filename[i]=='/') { start_count = i+1; }
    }
    
    end_count = len;
/*
    for(unsigned int i=0;i<len;i++)
    {
        if((filename[i]=='.')&&(filename[i+1]=='r')&&(filename[i+2]=='u')&&(filename[i+3]=='n'))
        { end_count = i; }
    }
*/
    strcpy(name,"NoName");

    if((end_count-start_count)>0)
    {
        for(unsigned int i=start_count;i<end_count;i++)
        { name[i-start_count]=filename[i];}
        name[end_count-start_count]='\0';
    }
}

void Get_Date(char *date, char *filename)
{
    unsigned int len = strlen(filename);
    unsigned int check = 0;
    unsigned int i = 0;

    while ((i<(len-6))&&(check!=7))
    {
        check = 0;
        date[0] = filename[i];
      
        if ((date[0]=='0')||(date[0]=='1')) { check = check + 1; }

        for(unsigned int j=1;j<6;j++)
        {
            date[j]=filename[j+i];
            if ((date[j]>='0')&&(date[j]<='9')) { check = check + 1; }
        }

        if((filename[i+6]<'0')||(filename[i+6]>'9')) { check = check + 1; }

        i++;
    }
 
    if (check!=7)
    { strcpy(date,"NoDate"); }
    else
    { date[6] = '\0'; }
}

